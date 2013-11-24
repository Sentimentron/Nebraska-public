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
import java.sql.PreparedStatement;
import weka.core.Attribute;
import java.util.ArrayList;

import weka.classifiers.meta.FilteredClassifier;
import weka.filters.unsupervised.attribute.Remove;

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
        String query = "SELECT document_identifier, label FROM label_domains ORDER BY document_identifier, label ASC";
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

    public static Set<Integer> findDocIdsMatchingDomain(List<Integer> domain, Map<Integer, List<Integer>> docDomainMap) {
        Set<Integer> ret = new HashSet<Integer>();
        for (Map.Entry<Integer, List<Integer>> entry : docDomainMap.entrySet()) {
            //System.err.printf("%s %s %b\n", entry.getValue(), domain, entry.getValue().equals(domain));
            if (!entry.getValue().equals(domain)) continue;
            ret.add(entry.getKey());
        }
        return ret;
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

        Instances data = DataSource.read("data.arff");
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

        for (List<Integer> src_domain : domainCombos) {
            for (List<Integer> dest_domain : domainCombos) {
                Set<Integer> trainingIds = findDocIdsMatchingDomain(src_domain, docDomainMap);
                Set<Integer> testIds = findDocIdsMatchingDomain(dest_domain, docDomainMap);
                // Create a total set of instances for filtering
                Instances trainingInstances = DataSource.read("datawithid.arff");
                Instances evaluationInstances = DataSource.read("datawithid.arff");
                Instances allInstances = DataSource.read("datawithid.arff");
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
                    identifier = rs.getString("document_identifier");
                    // Construct the instance
                    tmp = new DenseInstance(3);
                    tmp.setDataset(trainingInstances);
                    tmp.setValue(0, identifier);
                    tmp.setValue(1, document);
                    tmp.setValue(2, label);
                    int intVal = rs.getInt("document_identifier");
                    if (trainingIds.contains(intVal)) {
                        System.err.printf("TRAINING: %d\n", intVal);
                        trainingInstances.add(tmp);
                    }
                    if (testIds.contains(intVal)) {
                        System.err.printf("TESTING: %d\n", intVal);
                        evaluationInstances.add(tmp);
                    }
                }
                Classifier userCls = AbstractClassifier.makeCopy(userClsBase);
                // Mark the nominal class
                trainingInstances.setClassIndex(trainingInstances.numAttributes() - 1);
                evaluationInstances.setClassIndex(evaluationInstances.numAttributes() - 1);

                StringToWordVector stwFilt = new StringToWordVector();
                stwFilt.setInputFormat(trainingInstances);
                FilteredClassifier vectorCls = new FilteredClassifier();
                vectorCls.setFilter(stwFilt);
                vectorCls.setClassifier(userCls);

                Remove rngFilt = new Remove();
                rngFilt.setInputFormat(trainingInstances);
                rngFilt.setAttributeIndices("first");
                FilteredClassifier cls = new FilteredClassifier();
                cls.setClassifier(vectorCls);
                cls.setFilter(rngFilt);

                // Randomize training data
                StringToWordVector filter = new StringToWordVector();
                Random rand = new Random(seed);
                trainingInstances.randomize(rand);

                // Build the classifier
                System.err.println("Building classifier...");
                cls.buildClassifier(trainingInstances);

                // Test the classifier
                rngFilt = new Remove();
                rngFilt.setInputFormat(evaluationInstances);
                rngFilt.setAttributeIndices("first");
                stwFilt = new StringToWordVector();
                Instances filteredRangeInstances = Filter.useFilter(evaluationInstances, rngFilt);
                stwFilt.setInputFormat(filteredRangeInstances);
                Instances tokenizedEvaluationInstances = Filter.useFilter(filteredRangeInstances, stwFilt);
                Evaluation eval = new Evaluation(tokenizedEvaluationInstances);
                eval.evaluateModel(cls, evaluationInstances);

                // output evaluation
                System.out.println();
                System.out.println("=== Setup ===");
                System.out.println("Classifier: " + cls.getClass().getName() + " " + Utils.joinOptions(cls.getOptions()));
                System.out.println("Dataset: " + data.relationName());
                System.out.println("Seed: " + seed);
                System.out.println("Instances (training):" + trainingInstances.size());
                System.out.println("Instances (evaluation):" + evaluationInstances.size());
                System.out.println();
                System.out.println("Area under curve: " + eval.areaUnderROC(0) + " (with respect to class index 0)");
                System.out.println("False Positive Rate: " + eval.falsePositiveRate(0) + " (with respect to class index 0)");
                System.out.println("False Negative Rate: " + eval.falseNegativeRate(0) + " (with respect to class index 0)");
                System.out.println("F Measure: " + eval.fMeasure(0) + " (with respect to class index 0)");
                System.out.println("Precision: " + eval.precision(0) + " (with respect to class index 0)");
                System.out.println("Recall: " + eval.recall(0) + " (with respect to class index 0)");
                System.out.println("True Negative Rate: " + eval.trueNegativeRate(0) + " (with respect to class index 0)");
                System.out.println("True Positive Rate: " + eval.truePositiveRate(0) + " (with respect to class index 0)");
                System.out.println();
            }
        }
    }

}