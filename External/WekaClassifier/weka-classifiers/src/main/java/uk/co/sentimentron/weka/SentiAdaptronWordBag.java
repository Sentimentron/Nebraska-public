import java.util.ArrayList;
import weka.core.Instances;
import weka.core.Attribute;
import weka.core.SparseInstance;
import java.sql.*;
import java.util.List;

public class SentiAdaptronWordBag {

    // public static void main(String args[]) {
    //     // Open connection to SQLite database
    //     Connection c = null;
    //     try {
    //         Class.forName("org.sqlite.JDBC");
    //         c = DriverManager.getConnection("jdbc:sqlite:turkgimpel.sqlite");
    //     } catch ( Exception e ) {
    //         System.err.println( e.getClass().getName() + ": " + e.getMessage() + "\nDo you have the SQLite JDBC in your classpath? get it at: https://bitbucket.org/xerial/sqlite-jdbc/downloads" );
    //         System.exit(1);
    //     }
    //     SentiAdaptronWordBag temp = new SentiAdaptronWordBag();
    //     int[] ids = {16,20,33};
    //     temp.constructInstances(c, ids);
    //     temp.printInstances();
    // }

    Instances data_set;
    int num_tokens;

    public SentiAdaptronWordBag() {
    }
    // TO DO: Add class label to instances
    public void constructInstances(Connection c, int[] document_identifiers) {
        // For each document in our data set retrive its tokenised form
        String query;
        String tokenised_form;
        determineAttributes(c);
        for(int i=0; i<document_identifiers.length; i++) {
            try {
                query = "SELECT tokenized_form FROM pos_gimpel WHERE document_identifier = " + document_identifiers[i];
                Statement stmt = c.createStatement();
                ResultSet rs = stmt.executeQuery(query);
                tokenised_form = rs.getString("tokenized_form");
                // Strip any tokens were not using from this tweet
                tokenised_form = removeTokens(tokenised_form);
                SparseInstance inst = new SparseInstance(num_tokens);
                inst.setDataset(data_set);
                for(String token : tokenised_form.split(" ")) {
                    inst.setValue(Integer.parseInt(token), 1);
                }
                data_set.add(inst);
            } catch(Exception e) {
                System.err.println( e.getClass().getName() + ": " + e.getMessage());
                e.printStackTrace();
                System.exit(1);
            }
        }
    }

    // Determine how many of the tokens were keeping and set the ones were keeping as attributes in the Instances object
    public void determineAttributes(Connection c) {
        // The initial implementation just keeps every token
        try {
            String query = "SELECT identifier FROM pos_tokens_gimpel";
            Statement stmt = c.createStatement();
            ResultSet rs = stmt.executeQuery(query);
            ArrayList<String> nom_values = new ArrayList<String>();
            nom_values.add("-1");
            nom_values.add("0");
            nom_values.add("1");
            Attribute label = new Attribute("label", nom_values);

            ArrayList<Attribute> attributes = new ArrayList<Attribute>();
            attributes.add(label);
            while ( rs.next() ) {
                int index = rs.getInt("identifier");
                Attribute temp = new Attribute(Integer.toString(index));
                attributes.add(temp);
            }
            data_set = new Instances("sentiment", attributes, num_tokens);
        } catch(Exception e) {
            System.err.println( e.getClass().getName() + ": " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }

    public void determineNumTokens(Connection c) {
        String query;
        Statement stmt;
        ResultSet rs;
        try {
            query = "SELECT COUNT(*) AS token_count FROM pos_tokens_gimpel";
            stmt = c.createStatement();
            rs = stmt.executeQuery(query);
            num_tokens = rs.getInt("token_count");
        } catch(Exception e) {
            System.err.println( e.getClass().getName() + ": " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }

    }

    public String removeTokens(String tokenised_form) {
        // remove any tokens were not keeping from the tweet
        return tokenised_form;
    }

    public Instances getData() {
        return data_set;
    }

    public void printInstances() {
        System.out.println(data_set);
    }

}
