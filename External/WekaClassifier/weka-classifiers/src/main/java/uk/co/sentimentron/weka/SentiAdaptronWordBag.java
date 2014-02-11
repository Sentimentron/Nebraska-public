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
import java.util.Map;
import java.util.AbstractMap.SimpleEntry;
import java.util.Map.Entry;
import weka.attributeSelection.PrincipalComponents;
import weka.attributeSelection.*;
import weka.attributeSelection.Ranker;
import weka.filters.unsupervised.attribute.ReplaceMissingWithUserConstant;
import weka.filters.supervised.instance.SpreadSubsample;

// Note the Word Bag assumes labels are 0,1,-1 anything else will make it cry.
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
    //     SentiAdaptronWordBag temp = new SentiAdaptronWordBag(c, "sanders", "gimpel", false);
    //     //int[] ids = {1,20,295};
    //     LinkedList ids = new LinkedList();
    //     ids.add(1);
    //     ids.add(2);
    //     ids.add(3);
    //     ids.add(4);
    //     temp.constructBigramInstances(c, ids);
    //     // temp.performPCA(false, -1, 0.95);
    //     // temp.keepTopN(10);
    //     // temp.keepWithEntropyAbove(0);
    //     temp.printInstances();
    // }

    Instances data_set;
    int num_tokens;
    // Tree containing all of the common english words we dont want to keep
    TreeSet<String> stop_words;
    // Linked list of attribute names to pass to the remove filter
    LinkedList<String> remove_names;
    // Tree map for storing word index -> frequency
    TreeMap<String,Integer> frequencies;
    // HashMap for storing attribute -> attributeData
    HashMap<String, AttributeData> att_data;
    boolean debug;
    // What corpus the data comes from (needed to determine the name of the labels table)
    String corpus;
    // What POS tagger was used (needed to determine the name of the pos table)
    String pos_tagger;
    // Keep track of the number of each class we have
    int positive;
    int negative;
    int neutral;
    // Connection object
    Connection c;

    public SentiAdaptronWordBag(Connection c, String corpus, String pos_tagger, boolean debug) {
        this.c = c;
        this.debug = debug;
        this.corpus = corpus;
        this.pos_tagger = pos_tagger;
        stop_words = new TreeSet<String>();
        remove_names = new LinkedList<String>();
        frequencies = new TreeMap<String, Integer>();
        att_data = new HashMap<String, AttributeData>();
        positive = 0;
        negative = 0;
        neutral = 0;
        loadStopWords();
    }

    public void buildWordBag(LinkedList document_identifiers, String ngram) {
        if(ngram.equals("unigrams")) {
            constructInstances(c, document_identifiers);
        } else if(ngram.equals("bigrams")) {
            constructBigramInstances(c, document_identifiers);
        } else {
            System.err.println("Unrecognised n-gram");
        }
    }

    public void constructInstances(Connection c, LinkedList document_identifiers) {
        String query;
        String tokenised_form;
        // Scan through all of our tokens and determine which ones to keep
        determineAttributes(c);
        if(debug) {
            System.out.println("Building Bag of Words from " + document_identifiers.size() + " documents");
        }
        try {
            for(int i=0; i<document_identifiers.size(); i++) {
                query = "SELECT tokenized_form, label FROM pos_"+pos_tagger+" NATURAL JOIN temporary_label_"+corpus+" WHERE document_identifier = " + document_identifiers.get(i);
                Statement stmt = c.createStatement();
                ResultSet rs = stmt.executeQuery(query);
                tokenised_form = rs.getString("tokenized_form");
                String class_label = rs.getString("label");
                SparseInstance inst = new SparseInstance(num_tokens);
                inst.setDataset(data_set);
                // Note that to save space the sparse instance class doesn't store the first nominal attribute so attributes with a class label of -1 wont show up in print statements
                inst.setClassValue(class_label);
                updateLabelCount(class_label);
                for(String token : tokenised_form.split(" ")) {
                    // Dont keep frequency counts of stop words
                    if(!remove_names.contains(token) ) {
                        updateFrequency(token);
                    }
                    // We need to update the count of the positive, negative and neutral instances for each attribute
                    updateAttributeLabelCounts(token, class_label);
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
            // Chances are if we end up here we couldn't find a label for the tweet
            System.out.println("Error finding a label for instance");
            e.printStackTrace();
        }
    }

    public void constructBigramInstances(Connection c, LinkedList document_identifiers) {
        String query;
        String tokenised_form;

        // ArrayList to temporarily store the instance objects in until we know enough to create the instances object
        ArrayList<SparseInstance> instance_store = new ArrayList<SparseInstance>();
        // Hastable to map the bigram to its position in the instances object so we know what index to insert at
        Hashtable<String, Integer> attribute_mapping = new Hashtable<String, Integer>();

        // ** Set up the instances object and add the class label attribute ** //
        // ArrayList to store the attributes in
        ArrayList<Attribute> attributes = new ArrayList<Attribute>();
        // Add the class label attribute
        ArrayList<String> nom_values = new ArrayList<String>();
        nom_values.add("-1");
        nom_values.add("0");
        nom_values.add("1");
        Attribute label = new Attribute("label", nom_values);
        attributes.add(label);
        data_set = new Instances("sentiment", attributes, 2);
        data_set.setClassIndex(0);

        // Counter of the position of the attribute, used later so we know where to mark the bigrams
        Integer att_index = 1;
        String keep = "((label)|";
        if(debug) {
            System.out.println("Building Bag of Words from " + document_identifiers.size() + " documents");
        }
        try {
            for(int i=0; i<document_identifiers.size(); i++) {
                // ** Get the rows from the database ** //
                query = "SELECT tokenized_form, label FROM pos_"+pos_tagger+" NATURAL JOIN temporary_label_"+corpus+" WHERE document_identifier = " + document_identifiers.get(i);
                Statement stmt = c.createStatement();
                ResultSet rs = stmt.executeQuery(query);
                tokenised_form = rs.getString("tokenized_form");
                String class_label = rs.getString("label");

                // ** A new SparseInstance to add the attributes to ** //
                SparseInstance inst = new SparseInstance(tokenised_form.length()-1);
                // Let WEKA know this instance belongs to the dataset
                inst.setDataset(data_set);
                // Note that to save space the sparse instance class doesn't store the first nominal attribute so attributes with a class label of -1 wont show up in print statements
                // Set the class label of this instance and update the bags internal counts
                inst.setClassValue(class_label);
                updateLabelCount(class_label);
                // Split the tweet into tokens on white space
                String[] tokens = tokenised_form.split(" ");
                for(int j=0; j<tokens.length-1; j++) {
                    // Bigrams are this token and the one following it and we store them as the tokens with a - between them
                    String bigram = tokens[j] + "-" + tokens[j+1];
                    updateFrequency(bigram);
                    // Keep track of this tokens index so we know what index to set to 1 later on
                    int pos;
                    // If its the first time we've seen this attribute then record its index and create a new attribute for it
                    if(attribute_mapping.get(bigram) == null) {
                        Attribute temp = new Attribute(bigram);
                        // Add this attribute to the Instances object at the next available position
                        data_set.insertAttributeAt(temp, att_index);
                        // We need to increment att_index now so make a note of what it was for use later on
                        pos = att_index;
                        keep = keep + "(" + bigram +")"+ "|";
                        // Keep track of what index this bigram was at so we can reuse it later
                        attribute_mapping.put(bigram, pos);
                        // Update att_index so we can slot a new attribute into the right place
                        att_index = att_index +1;
                    } else { // If we already had a record of this attribute grab its position so we can update the correct index
                        pos = attribute_mapping.get(bigram);
                    }
                    // Create an attribute data object for it so we do things like calculate the entropy of this attribute
                    att_data.put(bigram, new AttributeData(bigram));
                    // We need to update the count of the positive, negative and neutral instances for each attribute
                    updateAttributeLabelCounts(bigram, class_label);
                    // Finally make a note that this bigram occurs in this instance
                    inst.setValue(pos, 1);
                }
                // Now we've set all the attributes add it to our collection of instance objects so we can add it to the Instances object later
                instance_store.add(inst);
            }

            // Add all of our instance objects to the Instances set now (we couldnt do it earlier as ... (I have no idea but it doesn't work if you do))
            for(int i =0; i<instance_store.size(); i++) {
                data_set.add(instance_store.get(i));
            }
            // Lots of magic below, I have no idea why you have to do most of it but you do.
            try {
                BetterRemoveByName filter = new BetterRemoveByName();
                filter.setExpression(keep + ")");
                filter.setInvertSelection(true);
                filter.setInputFormat(data_set);
                data_set = Filter.useFilter(data_set, filter);
            } catch(Exception e) {
                e.printStackTrace();
            }

            ReplaceMissingWithUserConstant filter = new ReplaceMissingWithUserConstant();
            filter.setInputFormat(data_set);
            data_set = Filter.useFilter(data_set, filter);
        } catch(Exception e) {
            // Chances are if we end up here we couldn't find a label for the tweet
            System.out.println("Error finding a label for instance");
            e.printStackTrace();
        }
    }

    // THIS IS UNFINISHED AND DOES NOT WORK
    // // Default options would be to pass false, -1, 0.95
    // public void performPCA(boolean center_data, int max_attributes, double variance_covered) {
    //     AttributeSelection selector = new AttributeSelection();
    //     PrincipalComponents pca = new PrincipalComponents();
    //     pca.setCenterData(center_data);
    //     pca.setMaximumAttributeNames(max_attributes);
    //     pca.setVarianceCovered(variance_covered);
    //     Ranker ranker = new Ranker();
    //     selector.setEvaluator(pca);
    //     selector.setSearch(ranker);
    //     try {
    //         selector.SelectAttributes(data_set);
    //         data_set = selector.reduceDimensionality(data_set);
    //     } catch (Exception e ) {
    //       e.printStackTrace();
    //     }
    // }

    private void updateAttributeLabelCounts(String token, String label) {
        // Get the right attribute object from the hash table
        AttributeData temp = att_data.get(token);
        if(label.equals("1")) {
            temp.addPositive();
        } else if(label.equals("0")) {
            temp.addNeutral();
        } else if(label.equals("-1")) {
            temp.addNegative();
        }
    }

    Iterator valueIterator(TreeMap map) {
        Set set = new TreeSet(new Comparator<Map.Entry<String, Integer>>() {
            @Override
            public int compare(Entry<String, Integer> o1, Entry<String, Integer> o2) {
                return  o1.getValue().compareTo(o2.getValue()) > 0 ? -1 : 1;
            }
        });
        set.addAll(map.entrySet());
        return set.iterator();
    }

    // Removes all words but those with the N largest frequencies
    public void keepTopN(int n) {
        Iterator i = valueIterator(frequencies);
        int count = 0;
        // Dont filter the class label
        String exp = "(label|";
        boolean broke_early = false;
        while(i.hasNext()) {
            Entry<String,Integer> temp = (Entry<String,Integer>)i.next();
            if(count >= n) {
                broke_early=true;
                break;
            }
            if(debug) {
                System.out.println("Keeping " + temp.getKey() + " with frequency of " + temp.getValue());
            }
            exp = exp + temp.getKey() + "|";
            count++;
        }
        if(!broke_early) {
            System.out.println("Never had enough words to provide top " + n + " using top " + count);
        }
        exp = exp + ")";
        filterAllExcept(exp);
    }

    public void balanceClasses() {
        try {
            SpreadSubsample filter = new SpreadSubsample();
            filter.setDistributionSpread(1);
            filter.setInputFormat(data_set);
            data_set = Filter.useFilter(data_set, filter);
        } catch (Exception e) {
            System.err.println("Error balancing classes");
            e.printStackTrace();
        }

    }

    // Keeps all the attributes with an entropy below n
    public void keepWithEntropyBelow(double n) {
        // Get all of the values in the hashmap
        Collection<AttributeData> atts = att_data.values();
        Iterator<AttributeData> it = atts.iterator();
        String remove = "";
        while(it.hasNext()) {
            AttributeData temp = it.next();
            double entropy = temp.getEntropy(positive, negative, neutral);
            if(debug) {
                if(entropy >= 0) {
                    System.out.println("Entropy of " + temp.getToken() + " is " + entropy);
                }
            }
            // If the entropy of this attribute is greater than n remove it
            if(entropy > n) {
                if(debug) {
                    System.out.println("Removing " + temp.getToken() + " with entropy of " + entropy);
                }
                remove += temp.getToken() + "|";
            }
        }
        filterAll(remove);
    }

    // Keeps all the attributes with an entropy above n
    public void keepWithEntropyAbove(double n) {
        // Get all of the values in the hashmap
        Collection<AttributeData> atts = att_data.values();
        Iterator<AttributeData> it = atts.iterator();
        String remove = "";
        while(it.hasNext()) {
            AttributeData temp = it.next();
            double entropy = temp.getEntropy(positive, negative, neutral);
            if(debug) {
                if(entropy >= 0) {
                    System.out.println("Entropy of " + temp.getToken() + " is " + entropy);
                }
            }
            // If the entropy of this attribute is less than n remove it
            if(entropy < n) {
                if(debug) {
                    System.out.println("Removing " + temp.getToken() + " with entropy of " + entropy);
                }
                remove += temp.getToken() + "|";
            }
        }
        filterAll(remove);
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

    // Removes all of the attributes from the instances object specified in the regular expression
    private void filterAll(String exp) {
        try {
            BetterRemoveByName filter = new BetterRemoveByName();
            filter.setExpression(exp);
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
            if(debug) {
                System.out.println("Frequency of " + index +" is 1");
            }
        } else {
            Integer current = frequencies.get(index);
            frequencies.remove(index);
            current = current +1;
            frequencies.put(index, current);
            if(debug) {
                System.out.println("Frequency of " + index + " is " + current);
            }
        }
    }

    // Remove all of the words from our stopwords.txt from the dataset
    public void filterStopWords() {
        try {
            BetterRemoveByName filter = new BetterRemoveByName();
            String exp = "(";
            for(String name: remove_names) {
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
            String query = "SELECT identifier, token FROM pos_tokens_"+pos_tagger;
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
                    if( (word.length == 2) && (stop_words.contains(word[1]) ))  {
                        remove_names.add(Integer.toString(index));
                    }
                    // If its not a stop word create an attribute data object for it
                    att_data.put(Integer.toString(index), new AttributeData(Integer.toString(index)));
                } catch(Exception e) {
                    e.printStackTrace();
                }
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
            query = "SELECT COUNT(*) AS token_count FROM pos_tokens_"+pos_tagger;
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
        // Randomise the instances then return them
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

    private void updateLabelCount(String label) {
        if(label.equals("1")) {
            positive++;
        } else if(label.equals("0")) {
            neutral++;
        } else if(label.equals("-1")) {
            negative++;
        }
    }

    public int numPositive() {
        return positive;
    }

    public int numNegative() {
        return negative;
    }

    public int numNeutral() {
        return neutral;
    }



}
