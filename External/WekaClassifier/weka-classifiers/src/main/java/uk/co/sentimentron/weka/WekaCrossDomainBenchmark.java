import java.util.*;

import weka.core.Instances;
import weka.core.converters.ConverterUtils.DataSource;
import weka.core.converters.ConverterUtils.DataSink;
import weka.core.Utils;
import weka.classifiers.*;
import weka.classifiers.trees.*;
import weka.filters.Filter;
import weka.filters.supervised.attribute.AddClassification;
import weka.filters.unsupervised.attribute.StringToWordVector;
import weka.classifiers.AbstractClassifier;
import java.util.Random;
import java.sql.*;
import weka.core.DenseInstance;
import weka.core.SparseInstance;
import java.sql.PreparedStatement;
import weka.core.Attribute;
import java.util.ArrayList;
import weka.core.Instance;
import weka.classifiers.meta.FilteredClassifier;
import weka.filters.unsupervised.attribute.Remove;
import weka.filters.supervised.instance.SpreadSubsample;

/**
 * Tests every domain in the database against every other using the classifier specified. 
 *
 * Command-line parameters:
 * <ul>
 *    <li>-t SQLiteDatabase Path - the path to the SQLite database with the data</li>
 *    <li>-T String - The name of the POS-tagged table to read from</li>
 *    <li>-L String - The name of the temporary label table to read from</li>
 *    <li>-x int - the number of folds to use</li>
 *    <li>-s int - the seed for the random number generator</li>
 *    <li>-c int - the class index, "first" and "last" are accepted as well;
 *    "last" is used by default</li>
 *    <li>-W classifier - classname and options, enclosed by double quotes;
 *    the classifier to cross-validate</li>
 *    <li>-R String - The name of the results table</li>
 *    <li>--version - print git SHA1 hash and exits
 * </ul>
 *
 * Example command-line:
 * <pre>
 * java BagOfWords -t ../../Data/Corpora/database.sqlite -c last -x 10 -s 1 -W "weka.classifiers.trees.J48 -C 0.25"
 * </pre>
 *
 */

public class WekaCrossDomainBenchmark {

    public static Map<Integer, String> getDomainMap(Connection c) throws Exception {
        // Return a list of domains in the database
        System.err.println("Reading domains..."); 
        String query = "SELECT label_identifier, label FROM label_names_domains ORDER BY label_identifier ASC";
        Statement s = c.createStatement();
        ResultSet rs = s.executeQuery(query);
        Map<Integer, String> ret = new HashMap<Integer, String>();
        while (rs.next()) {
            int identifier = rs.getInt("label_identifier");
            String label = rs.getString("label");
            ret.put(identifier, label);
        }
        return ret;
    }

    public static Map<Integer, List<Integer>> getDocDomainMap(Connection c) throws Exception {
        System.err.println("Reading domain map...");
        String query = "SELECT document_identifier, label FROM label_domains ORDER BY label ASC";
        Statement s = c.createStatement();
        ResultSet rs = s.executeQuery(query);
        Map<Integer, List<Integer>> ret = new HashMap<Integer, List<Integer>>();
        while (rs.next()) {
            int key = rs.getInt("document_identifier");
            int label = rs.getInt("label");
            if (!ret.containsKey(key)) {
                ret.put(key, new ArrayList<Integer>());
            }
            List<Integer> appendTo = ret.get(key);
            appendTo.add(label);
        }
        return ret;
    }

    public static List<List<Integer>> getDomainCombos(Map<Integer, List<Integer>> domainMap) {
        System.err.println("Reading domain combos...");
        List<List<Integer>> ret = new ArrayList<List<Integer>>();
        for (List<Integer> v : domainMap.values()) {
            boolean matched = false;
            for (List<Integer> candidate : ret) {
                if (candidate.equals(v)) {
                    matched = true;
                    break;
                }
            }
            if (matched) continue;
            ret.add(v);
        }
        return ret;
    }

    public static Set<Integer> findDocIdsMatchingDomain(int domain, Map<Integer, List<Integer>> docDomainMap) {
        Set<Integer> ret = new HashSet<Integer>();
        for (Map.Entry<Integer, List<Integer>> entry : docDomainMap.entrySet()) {
            //System.err.printf("%s %s %b\n", entry.getValue(), domain, entry.getValue().equals(domain));
            if (!entry.getValue().contains(domain)) continue;
            ret.add(entry.getKey());
        }
        return ret;
    }

    public static Map<Integer, String> getPosTags(Connection c, String posTable) throws Exception {
        System.err.println("Reading pos map...");
        String queryTemplate = "SELECT identifier, token FROM pos_tokens_%1$s ASC";
        String query = String.format(queryTemplate, posTable);
        Statement s = c.createStatement();
        Map<Integer, String> ret = new HashMap<Integer, String>();
        ResultSet rs = s.executeQuery(query);
        while (rs.next()) {
            int identifier = rs.getInt("identifier");
            String token = rs.getString("token");
            ret.put(identifier, token);
        }
        return ret;
    }

    public static void copyInstanceToInstances(Instances raw, String cls, String document) {
        double[] instanceValue = new double[raw.numAttributes()];
        instanceValue[1] = raw.attribute(1).addStringValue(document);
        if (cls.equals("-1")) {
            instanceValue[0] = 0;
        }
        else {
            instanceValue[0] = 1;
        }
        raw.add(new DenseInstance(1.0, instanceValue));
    }

    public static void main(String[] args) throws Exception {

        for (String s : args) {
          if (s.equals("--version")) {
            System.out.println(VersionReader.getGitSha1());
            System.exit(0);
          }
        }

        // READ COMMAND LINE PARAMS
        String posTable = Utils.getOption("T", args);
        String labelTable = Utils.getOption("L", args);

        String queryTemplate = "SELECT tokenized_form AS document, label FROM pos_%1$s NATURAL JOIN temporary_label_%2$s";
        String query = String.format(queryTemplate, posTable, labelTable);

        // Parse classifier options
        String[] tmpOptions = Utils.splitOptions(Utils.getOption("W", args));
        String className = tmpOptions[0];
        tmpOptions[0] = "";

        // Create the classifier
        AbstractClassifier userClsBase = (AbstractClassifier) Utils.forName(AbstractClassifier.class, className, tmpOptions);

        // Read in our data from the SQLite file whose path is specified from the -t parameter
        Connection c = null;
        try {
          Class.forName("org.sqlite.JDBC");
          c = DriverManager.getConnection("jdbc:sqlite:" + Utils.getOption("t", args));
        } catch ( Exception e ) {
          System.err.println( e.getClass().getName() + ": " + e.getMessage() + "\nDo you have the SQLite JDBC in your classpath? get it at: https://bitbucket.org/xerial/sqlite-jdbc/downloads" );
          System.exit(1);
        }

        // Parse other options
        int seed = Integer.parseInt(Utils.getOption("s", args));

        // Read the human-readable domain names
        Map<Integer, String> domainNames = getDomainMap(c);
        Map<Integer, List<Integer>> docDomainMap = getDocDomainMap(c);
        List<List<Integer>> domainCombos = getDomainCombos(docDomainMap);
        Map<Integer, String> posMap = getPosTags(c, posTable);
        int max = domainNames.size() * domainNames.size();
        int cur = 0;

        for (int src_domain : domainNames.keySet()) {
            for (int dest_domain : domainNames.keySet()) {
                cur++;
                System.err.printf("Progress: %.2f %%\n", cur * 100.0 / max);
                Set<Integer> trainingIds = findDocIdsMatchingDomain(src_domain, docDomainMap);
                Set<Integer> testIds = findDocIdsMatchingDomain(dest_domain, docDomainMap);

                if (trainingIds.size() < 100 || testIds.size() < 100) continue;

                // Create a total set of instances for filtering
                Instances trainingInstances = DataSource.read("dataclassfirst.arff");
                Instances evaluationInstances = DataSource.read("dataclassfirst.arff");
                Instances allInstances = DataSource.read("dataclassfirst.arff");
                queryTemplate = "SELECT document_identifier, tokenized_form AS document, label FROM pos_%1$s NATURAL JOIN temporary_label_%2$s";
                query = String.format(queryTemplate, posTable, labelTable);
                Statement stmt = c.createStatement();
                ResultSet rs = stmt.executeQuery(query);
                // Build training instances set
                while ( rs.next() ) {
                    String document, label, identifier;
                    DenseInstance tmp;
                    // Read database values
                    document = rs.getString("document");
                    label = rs.getString("label");
                    int intVal = rs.getInt("document_identifier");
                    
                    if (testIds.contains(intVal)) { 
                        copyInstanceToInstances(evaluationInstances, label, document);
                    }
                    else if (trainingIds.contains(intVal)) {
                        copyInstanceToInstances(trainingInstances, label, document);
                    }

                }
                if (trainingInstances.size() < 100 || evaluationInstances.size() < 100) continue;

                // Mark the nominal class
                trainingInstances.setClassIndex(0);
                evaluationInstances.setClassIndex(0);

                SpreadSubsample filtSample = new SpreadSubsample();
                filtSample.setInputFormat(trainingInstances);
                filtSample.setDistributionSpread(1);
                trainingInstances = Filter.useFilter(trainingInstances, filtSample);

                if (trainingInstances.size() < 100 || evaluationInstances.size() < 100) continue;

                AbstractClassifier cls = (AbstractClassifier) Utils.forName(AbstractClassifier.class, className, tmpOptions);

                FilteredClassifier filteredClassifier = new FilteredClassifier(); 
                StringToWordVector filter = new StringToWordVector(1);
                filter.setInputFormat(trainingInstances);
                filteredClassifier.setFilter(filter); 
                filteredClassifier.setClassifier(cls);

                System.err.println("Building classifier...");
                trainingInstances.randomize(new Random(seed));
                filteredClassifier.buildClassifier(trainingInstances); 

                // Test the classifier
                Evaluation eval = new Evaluation(evaluationInstances);
                eval.evaluateModel(cls, evaluationInstances);

                // output evaluation
                System.out.println();
                System.out.println("=== Setup ===");
                System.out.println("Classifier: " + cls.getClass().getName() + " " + Utils.joinOptions(cls.getOptions()));
                System.out.println("Dataset: " + trainingInstances.relationName());
                System.out.println("Seed: " + seed);
                System.out.println("Instances (training):" + trainingInstances.size());
                System.out.println("Instances (evaluation):" + evaluationInstances.size());
                System.out.println();
                System.out.println(eval.toSummaryString());
                System.out.println("Area under curve: " + eval.areaUnderROC(0) + " (with respect to class index 0)");
                System.out.println("False Positive Rate: " + eval.falsePositiveRate(0) + " (with respect to class index 0)");
                System.out.println("False Negative Rate: " + eval.falseNegativeRate(0) + " (with respect to class index 0)");
                System.out.println("F Measure: " + eval.fMeasure(0) + " (with respect to class index 0)");
                System.out.println("Precision: " + eval.precision(0) + " (with respect to class index 0)");
                System.out.println("Recall: " + eval.recall(0) + " (with respect to class index 0)");
                System.out.println("True Negative Rate: " + eval.trueNegativeRate(0) + " (with respect to class index 0)");
                System.out.println("True Positive Rate: " + eval.truePositiveRate(0) + " (with respect to class index 0)");
                System.out.println();
                System.out.println("Training domain: " + domainNames.get(src_domain));
                System.out.println("Testing domain: " + domainNames.get(dest_domain));

                String results = "INSERT INTO results(classifier, folds, seed, correctly_classified_instances, incorrectly_classified_instances, percent_correctly_classified, percent_incorrectly_classified, mean_absolute_error, root_mean_squared_error, relative_absolute_error, root_relative_squared_error, total_number_of_instances, area_under_curve, false_positive_rate, false_negative_rate, f_measure, precision, recall, true_negative_rate, true_positive_rate, train_domain, test_domain) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
                PreparedStatement insertResults = c.prepareStatement(results);
                insertResults.setString(1, cls.getClass().getName() + " " + Utils.joinOptions(cls.getOptions()));
                insertResults.setInt(2, 0);
                insertResults.setInt(3, seed);
                insertResults.setDouble(4, eval.correct());
                insertResults.setDouble(5, eval.incorrect());
                insertResults.setDouble(6, eval.pctCorrect());
                insertResults.setDouble(7, eval.pctIncorrect());
                insertResults.setDouble(8, eval.meanAbsoluteError());
                insertResults.setDouble(9, eval.rootMeanSquaredError());
                insertResults.setDouble(10, eval.relativeAbsoluteError());
                insertResults.setDouble(11, eval.rootRelativeSquaredError());
                insertResults.setDouble(12, eval.numInstances());
                insertResults.setDouble(13, eval.areaUnderROC(0));
                insertResults.setDouble(14, eval.falsePositiveRate(0));
                insertResults.setDouble(15, eval.falseNegativeRate(0));
                insertResults.setDouble(16, eval.fMeasure(0));
                insertResults.setDouble(17, eval.precision(0));
                insertResults.setDouble(18, eval.recall(0));
                insertResults.setDouble(19, eval.trueNegativeRate(0));
                insertResults.setDouble(20, eval.truePositiveRate(0));
                insertResults.setString(21, domainNames.get(src_domain));
                insertResults.setString(22, domainNames.get(dest_domain));
                insertResults.executeUpdate();
                insertResults.close();

            }
        }
    }

}