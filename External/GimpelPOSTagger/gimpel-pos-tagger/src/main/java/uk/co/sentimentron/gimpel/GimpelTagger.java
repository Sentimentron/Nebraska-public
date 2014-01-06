import java.util.List;
import java.util.ArrayList;
import java.util.*;
import cmu.arktweetnlp.Tagger;
import java.sql.*;
import java.lang.StringBuffer;
import java.util.Hashtable;

public class GimpelTagger {

    // Path to the SQLite database
    public String path;
    // Name of the table to read input documents from
    public String input_table;
    // Name of the table to insert tokens into
    public String token_table;
    // Name of the table to insert POS tagged documents into
    public String string_table;
    /*
        0 Path to SQlite database file
        1 Name of the table to read the input from
        2 Name of the table to store the tokens in
        3 Name of the table to store the POS tagged document in
     */
    public static void main(String args[]) {
        for (String s : args) {
          if (s.equals("--version")) {
            System.out.println(VersionReader.getGitSha1());
            System.exit(0);
          }
        }

        GimpelTagger tagger = new GimpelTagger();

        tagger.path = args[0];
        tagger.input_table = args[1];
        tagger.token_table = args[2];
        tagger.string_table = args[3];
        tagger.tokenise();

    }

    public void tokenise() {
        Tagger tokeniser = loadTagger("model.20120919");
        Connection conn = connectToDatabase(path);
        // Hashtable for storing string -> row id mappings
        Hashtable<String, Integer> stored_tokens = new Hashtable<String, Integer>();

        // Itterate over each document in the input database and tag it
        String query = "SELECT * FROM " + input_table;
        try {

            conn.setAutoCommit(false);
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(query);
            // Yes we really have to do this to count how many results we have :(
            int total_results = 0;
            int done_so_far=0;
            while(rs.next()) {
                total_results++;
            }
            rs = stmt.executeQuery(query);
            while(rs.next() ) {
                if ((done_so_far % 5) == 0) System.err.printf("POS Tagging... (%.2f%% done)\r", done_so_far * 100.f / total_results);
                done_so_far++;
                // POS tag this document
                List<cmu.arktweetnlp.Tagger.TaggedToken> tokens = new ArrayList<cmu.arktweetnlp.Tagger.TaggedToken>();
                tokens = tokeniser.tokenizeAndTag(rs.getString("document"));
                StringBuffer tagged_string = new StringBuffer();
                // For each token we got store it in the DB and build up the tokenised version of the document
                Iterator itt = tokens.iterator();
                while(itt.hasNext()) {
                    // Retrieve the next token from the iterator 
                    cmu.arktweetnlp.Tagger.TaggedToken temp = (cmu.arktweetnlp.Tagger.TaggedToken)itt.next();
                    String taggedToken = String.format("%1$s/%2$s", temp.tag, temp.token);
                    // Stored tokens contains the tokens already stored 
                    Integer index = stored_tokens.get(taggedToken);
                    if( index == null) {
                        // We dont already have this token so throw it in the database
                        String insert_tag = "INSERT INTO %1$s(token) VALUES(?)";
                        String insert_tag_query = String.format(insert_tag, token_table);
                        PreparedStatement insert_tag_query_with_variable = conn.prepareStatement(insert_tag_query);
                        insert_tag_query_with_variable.setString(1, taggedToken);
                        insert_tag_query_with_variable.executeUpdate();
                        ResultSet meta = insert_tag_query_with_variable.getGeneratedKeys();
                        int id = meta.getInt("last_insert_rowid()");
                        // Add the token to the ouput string
                        stored_tokens.put(taggedToken, id);
                        tagged_string.append(id);
                        tagged_string.append(" ");
                    } else {
                        // We have this token so add it to our string
                        tagged_string.append(index);
                        tagged_string.append(" ");
                    }

                }
                // We've now inserted all the tokens and built up the tokenised string so insert the tokenised string
                String insert_pos_tagged_document = "INSERT INTO %1$s (document_identifier, tokenized_form) VALUES(%2$s, \"%3$s\")";
                String pos_tagged_document_query = String.format(insert_pos_tagged_document, string_table, rs.getString("identifier"), tagged_string.toString());
                Statement insert_tagged_string_statement = conn.createStatement();
                insert_tagged_string_statement.execute(pos_tagged_document_query);
            }
            conn.commit();
        } catch(Exception e) {
            System.err.println( e.getClass().getName() + ": " + e.getMessage() + "\n");
            e.printStackTrace();
            System.exit(1);
        }

    }

    private Connection connectToDatabase(String database) {
        // Open connection to SQLite database
        Connection c = null;
        try {
            Class.forName("org.sqlite.JDBC");
            c = DriverManager.getConnection("jdbc:sqlite:" + database);
        } catch ( Exception e ) {
            System.err.println( e.getClass().getName() + ": " + e.getMessage() + "\nDo you have the SQLite JDBC in your classpath? get it at: https://bitbucket.org/xerial/sqlite-jdbc/downloads" );
            System.exit(1);
        }
        return c;
    }

    private Tagger loadTagger(String model) {
        Tagger tokeniser = new Tagger();
        try {
            tokeniser.loadModel(model);
        } catch(Exception e) {
            System.err.println( e.getClass().getName() + ": " + e.getMessage() + "\n");
            e.printStackTrace();
            System.exit(1);
        }
        return tokeniser;
    }

}
