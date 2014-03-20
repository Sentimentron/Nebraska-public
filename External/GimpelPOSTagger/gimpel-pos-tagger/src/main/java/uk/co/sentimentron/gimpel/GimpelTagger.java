import java.util.List;
import java.util.ArrayList;
import java.util.*;
import cmu.arktweetnlp.RawTagger;
import cmu.arktweetnlp.RawTwokenize;
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
    public String offset_table;
    public String norm_table;
    /*
        0 Path to SQlite database file
        1 Name of the table to read the input from
        2 Name of the table to store the tokens in
        3 Name of the table to store the POS tagged document in
        4 name of the table used to store token offset and confidence info
        5 name of the table used to store normalised document format
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
        tagger.offset_table  = args[4];
        tagger.norm_table   = args[5];
        tagger.tokenise();

    }

    public void tokenise() {
        RawTagger tokeniser = loadTagger("model.20120919");
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
                List<cmu.arktweetnlp.RawTagger.TaggedToken> tokens = new ArrayList<cmu.arktweetnlp.RawTagger.TaggedToken>();
                tokens = tokeniser.tokenizeAndTag(rs.getString("document"));
                // Insert normalised database form
                String normalisedDocumentText = RawTwokenize.normalizeTextForTagger(rs.getString("document"));
                String insertDocStmt = "INSERT INTO %1$s(document_identifier, document) VALUES (%2$s, ?)";
                String insertDocFmt  = String.format(insertDocStmt, this.norm_table, rs.getString("identifier"));
                PreparedStatement normStmt = conn.prepareStatement(insertDocFmt);
                normStmt.setString(1, normalisedDocumentText);
                normStmt.execute();
                // Build up the tagged string
                StringBuffer tagged_string = new StringBuffer();
                // For each token we got store it in the DB and build up the tokenised version of the document
                Iterator itt = tokens.iterator();
                while(itt.hasNext()) {
                    // Retrieve the next token from the iterator 
                    cmu.arktweetnlp.RawTagger.TaggedToken temp = (cmu.arktweetnlp.RawTagger.TaggedToken)itt.next();
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
                    // Insert TaggedToken information into the database 
                    String insertTknStmt = "INSERT INTO %1$s(document_identifier, start, end, word, tag, confidence) VALUES (%2$s, ?, ?, ?, ?, ?)";
                    String insertTknStmtQ = String.format(insertTknStmt, offset_table, rs.getString("identifier"));
                    PreparedStatement tknStmt = conn.prepareStatement(insertTknStmtQ);
                    tknStmt.setInt(1, temp.span.first);
                    tknStmt.setInt(2, temp.span.second);
                    tknStmt.setString(3, temp.token);
                    tknStmt.setString(4, temp.tag);
                    tknStmt.setDouble(5, temp.confidence);
                    tknStmt.execute();
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

    private RawTagger loadTagger(String model) {
        RawTagger tokeniser = new RawTagger();
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
