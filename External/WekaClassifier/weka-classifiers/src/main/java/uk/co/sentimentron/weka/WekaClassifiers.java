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
import weka.core.Attribute;
import java.util.ArrayList;

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
 *    <li>--version - print git SHA1 hash and exits
 * </ul>
 *
 * Example command-line:
 * <pre>
 * java BagOfWords -t ../../Data/Corpora/database.sqlite -c last -x 10 -s 1 -W "weka.classifiers.trees.J48 -C 0.25"
 * </pre>
 *
 */
public class WekaClassifiers {

  public static void main(String[] args) throws Exception {

    for (String s : args) {
      if (s.equals("--version")) {
        System.out.println(VersionReader.getGitSha1());
        System.exit(0);
      }
    }

    // Parse command line arguments 
    String posTable = Utils.getOption("T", args);
    String labelTable = Utils.getOption("L", args);

    String queryTemplate = "SELECT tokenized_form AS document, label FROM pos_%1$s NATURAL JOIN temporary_label_%2$s";
    String query = String.format(queryTemplate, posTable, labelTable); 

    Instances data = DataSource.read("data.arff");
    // Read in our data from the SQLite file whose path is specified from the -t parameter
    Connection c = null;
    try {
      Class.forName("org.sqlite.JDBC");
      c = DriverManager.getConnection("jdbc:sqlite:" + Utils.getOption("t", args));
    } catch ( Exception e ) {
      System.err.println( e.getClass().getName() + ": " + e.getMessage() + "\nDo you have the SQLite JDBC in your classpath? get it at: https://bitbucket.org/xerial/sqlite-jdbc/downloads" );
      System.exit(0);
    }

    Statement stmt = c.createStatement();
    ResultSet rs = stmt.executeQuery(query);

    while ( rs.next() ) {
      DenseInstance temp = new DenseInstance(2);
      temp.setDataset(data);
      String label = rs.getString("label");
      String  document = rs.getString("document");
      temp.setValue(0, document);
      temp.setValue(1, label);
      data.add(temp);
    }
    rs.close();
    stmt.close();
    c.close();

    String clsIndex = Utils.getOption("c", args);
    if (clsIndex.length() == 0)
      clsIndex = "last";
    if (clsIndex.equals("first"))
      data.setClassIndex(0);
    else if (clsIndex.equals("last"))
      data.setClassIndex(data.numAttributes() - 1);
    else
      data.setClassIndex(Integer.parseInt(clsIndex) - 1);

    // classifier
    String[] tmpOptions;
    String classname;
    tmpOptions     = Utils.splitOptions(Utils.getOption("W", args));
    classname      = tmpOptions[0];
    tmpOptions[0]  = "";
    AbstractClassifier cls = (AbstractClassifier) Utils.forName(AbstractClassifier.class, classname, tmpOptions);
; 
    // other options
    int seed  = Integer.parseInt(Utils.getOption("s", args));
    int folds = Integer.parseInt(Utils.getOption("x", args));

    StringToWordVector filter = new StringToWordVector();

    // randomize data
    Random rand = new Random(seed);
    Instances randData = new Instances(data);
    try {
      filter.setInputFormat(randData);
      filter.setAttributeIndices("1");
      randData = Filter.useFilter(randData, filter);
    } catch (Exception e) {
      System.out.println(e.toString());
    }

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
      Classifier clsCopy = AbstractClassifier.makeCopy(cls);
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
  }
}
