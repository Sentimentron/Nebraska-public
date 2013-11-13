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
import weka.filters.unsupervised.attribute.Remove;
import java.util.TreeSet;

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

        // Create a total set of instances for filtering
        Instances allInstances = DataSource.read("datawithid.arff");
        Instances trainingInstances = DataSource.read("datawithid.arff");
        Instances evaluationInstances = DataSource.read("datawithid.arff");
        TreeSet<Integer> trainingIds = new TreeSet<Integer>();
        TreeSet<Integer> evaluationIds = new TreeSet<Integer>();

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
            String document, label, identifier;
            DenseInstance tmp;
            // Read database values
            document = rs.getString("tokenized_form");
            label = rs.getString("class_label");
            identifier = rs.getString("document_identifier");
            // Construct the instance
            tmp = new DenseInstance(3);
            tmp.setDataset(trainingInstances);
            tmp.setValue(0, identifier);
            tmp.setValue(1, document);
            tmp.setValue(2, label);
            // Add instance to relevant tracking structures
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
            String document, identifier;
            DenseInstance tmp;
            // Read database results
            document = rs.getString("tokenized_form");
            identifier = rs.getString("document_identifier");
            // Construct the instance
            tmp = new DenseInstance(3);
            tmp.setDataset(evaluationInstances);
            tmp.setValue(0, identifier);
            tmp.setValue(1, document);
            tmp.setValue(2, 0);
            // Add to tracking structures
            evaluationInstances.add(tmp);
        }

        // Mark the nominal class
        trainingInstances.setClassIndex(trainingInstances.numAttributes() - 1);
        evaluationInstances.setClassIndex(evaluationInstances.numAttributes() - 1);

        // Parse classifier options
        String[] tmpOptions = Utils.splitOptions(Utils.getOption("W", args));
        String className = tmpOptions[0];
        tmpOptions[0] = "";

        // Create the classifier
        AbstractClassifier userCls = (AbstractClassifier) Utils.forName(AbstractClassifier.class, className, tmpOptions);

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

        // Parse other options
        int seed = Integer.parseInt(Utils.getOption("s", args));

        // Randomize training data
        StringToWordVector filter = new StringToWordVector();
        Random rand = new Random(seed);
        trainingInstances.randomize(rand);

        // Build the classifier
        System.err.println("Building classifier...");
        cls.buildClassifier(trainingInstances);

        queryTemplate = "INSERT INTO classification_%1$s VALUES (%2$s, %3$s, %4$s)";

        // label instances
        System.err.print("Labelling... (0.00% done)\r");
        int numInstances = evaluationInstances.numInstances();
        for (int i = 0; i < numInstances; i++) {

            double clsLabel;
            DenseInstance instance = (DenseInstance)evaluationInstances.instance(i);

            if ((i % 5) == 0) System.err.printf("Labelling... (%.2f%% done)\r", i * 100.f / numInstances);
            clsLabel = cls.classifyInstance(instance);
            instance.setClassValue(clsLabel);

            double[] distribution = cls.distributionForInstance(instance);
            Attribute identityAttr = instance.attribute(0);
            String identityStr = instance.stringValue(identityAttr);
            // Attribute classAttr = instance.attribute(evaluationInstances.numAttributes() - 1);
            // String classStr = instance.stringValue(classAttr);

            query = String.format(queryTemplate, outputTable, identityStr, distribution[0], distribution[1]);
            stmt = c.createStatement();
            stmt.execute(query);
        }
        System.err.println("Labelling... (100% done)");
        System.err.println("Committing changes...");
        c.close();
    }

}
