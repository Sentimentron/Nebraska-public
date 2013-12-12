import java.util.ArrayList;
import java.util.TreeMap;
import java.util.NavigableSet;
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
import java.util.*;

public class SentiAdaptronWordBag {

    public static void main(String args[]) {
        // Open connection to SQLite database
        Connection c = null;
        try {
            Class.forName("org.sqlite.JDBC");
            c = DriverManager.getConnection("jdbc:sqlite:turkgimpel.sqlite");
        } catch ( Exception e ) {
            System.err.println( e.getClass().getName() + ": " + e.getMessage() + "\nDo you have the SQLite JDBC in your classpath? get it at: https://bitbucket.org/xerial/sqlite-jdbc/downloads" );
            System.exit(1);
        }
        SentiAdaptronWordBag temp = new SentiAdaptronWordBag(true);
        int[] ids = {16}; //{16,20,33};
        temp.constructInstances(c, ids);
        //temp.keepTopN(4);
        temp.printInstances();
    }

    Instances data_set;
    int num_tokens;
    // Tree containing all of the common english words we dont want to keep
    TreeSet<String> stop_words;
    // Linked list of attribute names to pass to the remove filter
    LinkedList<String> remove_names;
    // Tree map for storing word index -> frequency
    TreeMap<String,Integer> frequencies;
    boolean debug;

    public SentiAdaptronWordBag(boolean debug) {
        this.debug = debug;
        stop_words = new TreeSet<String>();
        remove_names = new LinkedList<String>();
        frequencies = new TreeMap<String, Integer>();
        loadStopWords();

    }
    // TO DO: Add class label to instances
    public void constructInstances(Connection c, int[] document_identifiers) {
        String query;
        String tokenised_form;
        // Scan through all of our tokens and determine which ones to keep
        determineAttributes(c);
        if(debug) {
            System.out.println("Building Bag of Words from " + document_identifiers.length + " documents");
        }
        try {
            for(int i=0; i<document_identifiers.length; i++) {
                query = "SELECT tokenized_form FROM pos_gimpel WHERE document_identifier = " + document_identifiers[i];
                Statement stmt = c.createStatement();
                ResultSet rs = stmt.executeQuery(query);
                tokenised_form = rs.getString("tokenized_form");
                SparseInstance inst = new SparseInstance(num_tokens);
                inst.setDataset(data_set);
                // Set the class index to 0 until we figure out how to do it properly
                inst.setClassValue("1");
                for(String token : tokenised_form.split(" ")) {
                    // Dont keep frequency counts of stop words
                    if(!stop_words.contains(token) ) {
                        updateFrequency(token);
                    }
                    inst.setValue(Integer.parseInt(token), 1);
                }
                data_set.add(inst);
            }
            if(debug) {
                System.out.println(countAttributes() + " attributes before removing stop words");
            }
            filterStopWords();
            if(debug) {
                System.out.println(countAttributes() + " attributes after removing stop words");
            }
        } catch(Exception e) {
            e.printStackTrace();
        }
    }

    // Removes all words but those with the N largest frequencies
    public void keepTopN(int n) {
        NavigableSet<String> ordered = frequencies.descendingKeySet();
        Iterator i = ordered.iterator();
        int count = 0;
        // Dont filter the class label
        String exp = "(label|";
        boolean broke_early = false;
        while(i.hasNext()) {
            if(count >= n) {
                broke_early=true;
                break;
            }
            String x = (String)i.next();
            exp = exp + x + "|";
            count++;
        }
        if(!broke_early) {
            System.out.println("Never had enough words to provide top " + n + " using top " + count);
        }
        exp = exp + ")";
        filterAllExcept(exp);
    }

    // Removes all of the attributes from the instances object except those specified in the regular expression
    private void filterAllExcept(String exp) {
        try {
            BetterRemoveByName filter = new BetterRemoveByName();
            filter.setExpression(exp);
            filter.setInvertSelection(true);
            filter.setInputFormat(data_set);
            data_set = Filter.useFilter(data_set, filter);
        } catch(Exception e) {
            e.printStackTrace();
        }
    }

    // Increment the frequency of an attributes occurence in our hashtable
    public void updateFrequency(String index) {
        if(frequencies.get(index) == null ) {
            frequencies.put(index, 1);
        } else {
            Integer current = frequencies.get(index);
            frequencies.remove(index);
            frequencies.put(index, new Integer(current+1));
        }
    }

    // Remove all of the words from our stopwords.txt from the dataset
    public void filterStopWords() {
        try {
            BetterRemoveByName filter = new BetterRemoveByName();
            String exp = "(";
            for(String name: remove_names) {
                // For reasons unknown to me the RemoveByName filter increments each index by 1 so decrement it here by 1
                int ind = Integer.parseInt(name);
                exp = exp + "|(" + ind + ")";

            }
            exp = exp + ")";
            filter.setExpression(exp);
            filter.setInputFormat(data_set);
            data_set = Filter.useFilter(data_set, filter);
        } catch(Exception e) {
            e.printStackTrace();
        }

    }

    // Add all of the tokens as attributes to our Instances object as we filter them out later.
    public void determineAttributes(Connection c) {
        try {
            String query = "SELECT identifier, token FROM pos_tokens_gimpel";
            Statement stmt = c.createStatement();
            ResultSet rs = stmt.executeQuery(query);
            ArrayList<Attribute> attributes = new ArrayList<Attribute>();
            // Add the class label attribute
            ArrayList<String> nom_values = new ArrayList<String>();
            nom_values.add("-1");
            nom_values.add("0");
            nom_values.add("1");
            Attribute label = new Attribute("label", nom_values);
            attributes.add(label);
            // Itterate over every token in the database and add it as an attribute
            while ( rs.next() ) {
                int index = rs.getInt("identifier");

                String token = rs.getString("token");

                String word[] = token.split("/");
                // Try catch is here due to tokens representing a / messing it up
                try {
                    // If this token is a stop word note the index and we'll remove it later
                    if( (stop_words.contains(word[1]) ))  {
                        remove_names.add(Integer.toString(index));
                    }
                } catch(Exception e) {}
                // The attribute is the index of the token
                Attribute temp = new Attribute(Integer.toString(index));
                attributes.add(temp);
            }
            data_set = new Instances("sentiment", attributes, num_tokens);
            data_set.setClassIndex(0);
        } catch(Exception e) {
            System.err.println( e.getClass().getName() + ": " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }

    // Reads the stop words from the stopwords.txt file and loads them into the tree.
    public void loadStopWords() {
        try {
            // Load in a list of stop words from stop_words.txt which is a list of words with each new word on a new line
            BufferedReader reader = new BufferedReader(new FileReader("stopwords.txt"));
            String line = null;
            int count = 0;
            while ((line = reader.readLine()) != null) {
                stop_words.add(line);
                count++;
            }
            if(debug) {
                System.out.println("Loaded " + count + " stop words");
            }
        } catch(Exception e) {
            e.printStackTrace();
        }
    }

    // Determines how many tokens are in our database.
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

    // Returns the instances object
    public Instances getData() {
        return data_set;
    }

    // Prints all of the instances in the data_set object. Output is the header info then tuple mapping indexes to values.
    public void printInstances() {
        System.out.println(data_set);
    }

    // Count the number of attributes in our dataset
    public int countAttributes() {
        Enumeration temp = data_set.enumerateAttributes();
        int count = 0;
        while( temp.hasMoreElements() ) {
            temp.nextElement();
            count++;
        }
        return count;
    }

}
