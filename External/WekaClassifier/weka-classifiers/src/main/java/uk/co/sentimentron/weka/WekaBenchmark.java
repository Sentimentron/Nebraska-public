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
import java.util.*;
import java.text.SimpleDateFormat;
import java.io.*;

/**
 * Performs a single run of cross-validation and adds the prediction on the
 * test set to the dataset.
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
public class WekaBenchmark {

  public static void main(String[] args) throws Exception {

    for (String s : args) {
      if (s.equals("--version")) {
        System.out.println(VersionReader.getGitSha1());
        System.exit(0);
      }
    }

    // Get a database connection so we can insert results later
    Connection c = null;
    try {
      Class.forName("org.sqlite.JDBC");
      c = DriverManager.getConnection("jdbc:sqlite:" + Utils.getOption("t", args));
    } catch ( Exception e ) {
      System.err.println( e.getClass().getName() + ": " + e.getMessage() + "\nDo you have the SQLite JDBC in your classpath? get it at: https://bitbucket.org/xerial/sqlite-jdbc/downloads" );
      System.exit(1);
    }

    // // Parse command line arguments
    // String posTable = Utils.getOption("T", args);
    // String labelTable = Utils.getOption("L", args);

    // // Get a list of documents to use in the BOW
    // String queryTemplate = "SELECT document_identifier FROM temporary_label_%2$s";
    // String query = String.format(queryTemplate, posTable, labelTable);Statement stmt = c.createStatement();
    // ResultSet rs = stmt.executeQuery(query);
    // LinkedList documents = new LinkedList();
    // while ( rs.next() ) {
    //   documents.add(rs.getInt("document_identifier"));
    // }
    // rs.close();
    // stmt.close();

    // // Make a new BagOfWords and let it handle constructing the instances object. (The final parameter turns debugging on, flip it to false to turn it off.)
    // SentiAdaptronWordBag wordBag = new SentiAdaptronWordBag(c, labelTable, posTable, false);
    // wordBag.buildWordBag(documents, "bigrams");
    // wordBag.balanceClasses();
    // //wordBag.buildWordBag(documents, "bigrams");
    // // Possible options to reduce attribute count
    // // wordBag.keepTopN(10);
    // // wordBag.keepWithEntropyAbove(0.4);
    // // wordBag.keepWithEntropyBelow(0.4);
    // Instances data = wordBag.getData();
    BufferedReader reader = null;
    try {
        reader = new BufferedReader( new FileReader("unigrams.arff"));
    } catch(Exception e) {
        e.printStackTrace();

    }
    Instances data = new Instances(reader);
    data.setClassIndex(data.numAttributes() - 1);
    // classifier
    String[] tmpOptions;
    String classname;
    tmpOptions     = Utils.splitOptions(Utils.getOption("W", args));
    classname      = tmpOptions[0];
    tmpOptions[0]  = "";
    AbstractClassifier cls = (AbstractClassifier) Utils.forName(AbstractClassifier.class, classname, tmpOptions);
    Classifier clsCopy = null;
    // other options
    int seed  = Integer.parseInt(Utils.getOption("s", args));
    int folds = Integer.parseInt(Utils.getOption("x", args));

    // randomize data
    Random rand = new Random(seed);
    Instances randData = new Instances(data);

    randData.randomize(rand);
    if (randData.classAttribute().isNominal())
      randData.stratify(folds);

    // perform cross-validation and add predictions
    Instances predictedData = null;
    Evaluation eval = new Evaluation(randData);
    for (int n = 0; n < folds; n++) {

      Instances train = randData.trainCV(folds, n);
      Instances test = randData.testCV(folds, n);

      // build and evaluate classifier
      clsCopy = AbstractClassifier.makeCopy(cls);
      clsCopy.buildClassifier(train);
      eval.evaluateModel(clsCopy, test);
    }

    // output evaluation
    System.out.println();
    System.out.println("=== Setup ===");
    System.out.println("Classifier: " + cls.getClass().getName() + " " + Utils.joinOptions(cls.getOptions()));
    System.out.println("Dataset: " + data.relationName());
    System.out.println("Folds: " + folds);
    System.out.println("Seed: " + seed);
    System.out.println();
    System.out.println(eval.toSummaryString("=== " + folds + "-fold Cross-validation ===", false));
    System.out.println("Area under curve: " + eval.areaUnderROC(0) + " (with respect to class index 0)");
    System.out.println("False Positive Rate: " + eval.falsePositiveRate(0) + " (with respect to class index 0)");
    System.out.println("False Negative Rate: " + eval.falseNegativeRate(0) + " (with respect to class index 0)");
    System.out.println("F Measure: " + eval.fMeasure(0) + " (with respect to class index 0)");
    System.out.println("Precision: " + eval.precision(0) + " (with respect to class index 0)");
    System.out.println("Recall: " + eval.recall(0) + " (with respect to class index 0)");
    System.out.println("True Negative Rate: " + eval.trueNegativeRate(0) + " (with respect to class index 0)");
    System.out.println("True Positive Rate: " + eval.truePositiveRate(0) + " (with respect to class index 0)");
    System.out.println();

    // Insert the results into the database
    String results = "INSERT INTO results(classifier, folds, seed, correctly_classified_instances, incorrectly_classified_instances, percent_correctly_classified, percent_incorrectly_classified, mean_absolute_error, root_mean_squared_error, relative_absolute_error, root_relative_squared_error, total_number_of_instances, area_under_curve, false_positive_rate, false_negative_rate, f_measure, precision, recall, true_negative_rate, true_positive_rate, negative_instances, positive_instances, neutral_instances) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
    PreparedStatement insertResults = c.prepareStatement(results);
    insertResults.setString(1, cls.getClass().getName() + " " + Utils.joinOptions(cls.getOptions()));
    insertResults.setInt(2, folds);
    insertResults.setInt(3,seed);
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
    // insertResults.setInt(21, wordBag.numNegative());
    // insertResults.setInt(22, wordBag.numPositive());
    // insertResults.setInt(23, wordBag.numNeutral());
    insertResults.executeUpdate();
    insertResults.close();
    c.close();

    // Save the model
    SimpleDateFormat simpleDateFormat = new SimpleDateFormat("ddMMyy-hhmmss.SSS");
    weka.core.SerializationHelper.write(classname+ "-" +simpleDateFormat.format(new java.util.Date() )+".model", clsCopy);
  }
}
