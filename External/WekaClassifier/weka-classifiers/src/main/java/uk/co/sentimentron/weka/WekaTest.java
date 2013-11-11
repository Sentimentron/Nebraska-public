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
import weka.core.SparseInstance;
import weka.core.DenseInstance;
import weka.core.Attribute;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import weka.classifiers.meta.FilteredClassifier; 
import weka.filters.unsupervised.instance.RemoveRange;

/**
 * Reads the training and test sets from table t, operate on POS-tagged table 
 * t
 *
 * Command-line parameters:
 * <ul>
 *    <li>-d SQLiteDatabase Path - the path to the SQLite database with the data</li>
 *    <li>-T String - The name of the POS-tagged table to read from</li>
 *    <li>-t String - The name of the training/classification label table</li>
 *    <li>-L String - The name of the temporary label table to read from</li>
 *    <li>-O String - The name of the temporary label table to output to</li>
 *    <li>-s int - the seed for the random number generator</li>
 *    <li>-W classifier - classname and options, enclosed by double quotes;
 *    the classifier to cross-validate</li>
 *    <li>--version - print git SHA1 hash and exits
 * </ul>
 */

public class WekaTest {

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
        String trainTestTable = Utils.getOption("t", args);
        String outputTable = Utils.getOption("O", args);

        // Create training + evaluation instances 
        Instances trainingInstances = DataSource.read("datawithid.arff");
        Instances evaluationInstances = DataSource.read("datawithid.arff");
        
        // Open connection to SQLite database
        Connection c = null;
        try {
            Class.forName("org.sqlite.JDBC");
            c = DriverManager.getConnection("jdbc:sqlite:" + Utils.getOption("d", args));
        } catch ( Exception e ) {
            System.err.println( e.getClass().getName() + ": " + e.getMessage() + "\nDo you have the SQLite JDBC in your classpath? get it at: https://bitbucket.org/xerial/sqlite-jdbc/downloads" );
            System.exit(1);
        }

        // Build and execute query to retrieve training instances + labels
        System.err.println("Reading training data...");
        String queryTemplate = "SELECT temporary_label_%2$s.document_identifier, tokenized_form, "
            + "temporary_label_%2$s.label AS class_label "
            + "FROM pos_%3$s NATURAL JOIN temporary_label_%2$s JOIN "
            + "temporary_label_%1$s ON temporary_label_%2$s.document_identifier = "
            + "temporary_label_%1$s.document_identifier "
            + "WHERE temporary_label_%1$s.label = 0";
        System.err.println(queryTemplate);
        String query = String.format(queryTemplate, trainTestTable, labelTable, posTable);
        System.err.println(query);
        Statement stmt = c.createStatement();
        ResultSet rs = stmt.executeQuery(query);
        // Build training instances set 
        while ( rs.next() ) {
            DenseInstance tmp = new DenseInstance(3);
            tmp.setDataset(trainingInstances);
            String document = rs.getString("tokenized_form");
            String label = rs.getString("class_label");
            int identifier = rs.getInt("document_identifier");
            tmp.setValue(0, identifier);
            tmp.setValue(1, document);
            tmp.setValue(2, label);
            trainingInstances.add(tmp);
        }

        // Build and execute query to retrieve test instances 
        System.err.println("Reading evaluation data...");
        queryTemplate = "SELECT tokenized_form, document_identifier FROM pos_%1$s "
            + "NATURAL JOIN temporary_label_%2$s "
            + "WHERE temporary_label_%2$s.label = 1";
        query = String.format(queryTemplate, posTable, trainTestTable);
        stmt = c.createStatement();
        rs = stmt.executeQuery(query);
        Map<DenseInstance, Integer> instanceMapping = new HashMap<DenseInstance, Integer>();
        Map<SparseInstance, Integer> sparseInstanceMapping = new HashMap<SparseInstance, Integer>();
        while ( rs.next() ) {
            DenseInstance tmp = new DenseInstance(3);
            tmp.setDataset(evaluationInstances);
            String document = rs.getString("tokenized_form");
            int identity = rs.getInt("document_identifier");
            tmp.setValue(0, identity);
            tmp.setValue(1, document);
            evaluationInstances.add(tmp);
        }

        trainingInstances.setClassIndex(trainingInstances.numAttributes() - 1);
        evaluationInstances.setClassIndex(evaluationInstances.numAttributes() - 1);

        // Parse classifier options 
        String[] tmpOptions = Utils.splitOptions(Utils.getOption("W", args));
        String className = tmpOptions[0];
        tmpOptions[0] = "";

        // Create the classifier 
        AbstractClassifier userCls = (AbstractClassifier) Utils.forName(AbstractClassifier.class, className, tmpOptions);
        FilteredClassifier cls = new FilteredClassifier();
        RemoveRange rFilter = new RemoveRange(); 
        rFilter.setInputFormat(trainingInstances);
        rFilter.setInstancesIndices("2-last");
        cls.setFilter(rFilter);
        cls.setClassifier(userCls);

        // Parse other options 
        int seed = Integer.parseInt(Utils.getOption("s", args));

        // Randomize and split data
        StringToWordVector filter = new StringToWordVector();
        Random rand = new Random(seed);
        Instances randTrainingInstances = new Instances(trainingInstances);
        filter.setInputFormat(randTrainingInstances);
        filter.setAttributeIndices("2");
        randTrainingInstances = Filter.useFilter(randTrainingInstances, filter);
        randTrainingInstances.randomize(rand);

        // Build the classifier 
        System.err.println("Building classifier...");
        cls.buildClassifier(randTrainingInstances);

        queryTemplate = "INSERT INTO classification_%1$s VALUES (%2$s, %3$d)";

        // label instances
        System.err.print("Labelling... (0.00% done)\r");
        for (int i = 0; i < evaluationInstances.numInstances(); i++) {

            double clsLabel; 
            DenseInstance instance = (DenseInstance)evaluationInstances.instance(i);
            SparseInstance splitInstance; 

            if(!filter.input(instance)) {
                throw new Exception("Failed to input word!");
            }
            splitInstance = (SparseInstance) filter.output();

            if ((i % 5) == 0) System.err.printf("Labelling... (%.2f done)\r", i * 100.f / evaluationInstances.numInstances());
            clsLabel = cls.classifyInstance(splitInstance);
            instance.setClassValue(clsLabel);

            Attribute identity = splitInstance.attribute(1);
            String identityStr = identity.value(0);

            query = String.format(queryTemplate, outputTable, identityStr, (int)clsLabel);
            stmt = c.createStatement();
            stmt.execute(query);
        }
        System.err.println("Labelling... (100% done)");
    }

}