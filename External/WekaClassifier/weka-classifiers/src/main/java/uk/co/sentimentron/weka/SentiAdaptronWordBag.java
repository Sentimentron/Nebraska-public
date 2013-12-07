import java.util.ArrayList;
import weka.core.Instances;
import weka.core.Attribute;
import weka.core.SparseInstance;
import java.sql.*;
import java.util.List;
import weka.filters.unsupervised.attribute.RemoveByName;
import weka.filters.Filter;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.TreeSet;
import java.util.LinkedList;
import java.util.Enumeration;

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
    //     //temp.printInstances();
    // }

    Instances data_set;
    int num_tokens;
    // Tree containing all of the common english words we dont want to keep
    TreeSet<String> stop_words;
    // Linked list of attribute names to pass to the remove filter
    LinkedList<String> remove_names;

    public SentiAdaptronWordBag() {
        stop_words = new TreeSet<String>();
        remove_names = new LinkedList<String>();
        loadStopWords();
    }
    // TO DO: Add class label to instances
    public void constructInstances(Connection c, int[] document_identifiers) {
        // For each document in our data set retrive its tokenised form
        String query;
        String tokenised_form;
        determineAttributes(c);
        try {
            for(int i=0; i<document_identifiers.length; i++) {
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
            }
            filterAttributes();
        } catch(Exception e) {
            e.printStackTrace();
        }
    }

    public void filterAttributes() {
        try {
            RemoveByName filter = new RemoveByName();
            String exp = "(";
            for(String name: remove_names) {
                exp = exp + "|(" + name + ")";
            }
            exp = exp + ")";
            filter.setExpression(exp);
            filter.setInputFormat(data_set);
            data_set = Filter.useFilter(data_set, filter);
        } catch(Exception e) {
            e.printStackTrace();
        }

    }

    // Determine how many of the tokens were keeping and set the ones were keeping as attributes in the Instances object
    public void determineAttributes(Connection c) {
        // The initial implementation just keeps every token
        try {
            String query = "SELECT identifier, token FROM pos_tokens_gimpel";
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
                String token = rs.getString("token");
                String word[] = token.split("/");

                try {
                    if( (stop_words.contains(word[1]) ))  {
                        remove_names.add(Integer.toString(index));
                    }
                } catch(Exception e) {}
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

    public void loadStopWords() {
        try {
            // Load in a list of stop words from stop_words.txt which is a list of words with each new word on a new line
            BufferedReader reader = new BufferedReader(new FileReader("stopwords.txt"));
            String line = null;
            while ((line = reader.readLine()) != null) {
                stop_words.add(line);
            }
        } catch(Exception e) {
            e.printStackTrace();
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

    public void countAttributes() {
        Enumeration temp = data_set.enumerateAttributes();
        int count = 0;
        while( temp.hasMoreElements() ) {
            temp.nextElement();
            count++;
        }
        System.out.println(count);
    }

}
