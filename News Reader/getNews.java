import java.io.InputStream;
import java.net.URL;
import java.net.URLConnection;


import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;

import org.w3c.dom.Document;
import org.w3c.dom.NodeList;

import java.sql.DriverManager;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.PreparedStatement;

public class getNews{
	
	public Connection con = null;
	public Statement statement= null;
	public String JDBC_DRIVER = "com.mysql.jdbc.Driver";
	public String username = "twitterstream",password = "rootfish";
	static String dbname = "jdbc:mysql://localhost/newsstream";
	
	public static void main(String[] args) {
		try{
				
			getNews news = new getNews();
			news.Connect();
			news.storeNews("http://rss.cnn.com/rss/edition_technology.rss", 2, "CNN");
			news.storeNews("http://mf.feeds.reuters.com/reuters/technologyNews", 2, "Reuters");
	
		}
		catch (Exception e){
			System.out.println("ahhh helll yeaa");	
		}
	}
	
	private void storeNews(String url1, int skip, String source){
		
		
		
		try{
				
			//open cnn tech feed
			URL url = new URL(url1);
			URLConnection conn = url.openConnection();
			
			//read xml file
			Document doc = parseXML(conn.getInputStream()); 
			
			NodeList titles = doc.getElementsByTagName("title");
			NodeList summary = doc.getElementsByTagName("description");
			
			for(int i = skip; i<titles.getLength()-1; i++){
				
				System.out.println("Printing Titles- " + titles.item(i).getTextContent());	
				
				
				
				String[] toInsert = summary.item(i-1).getTextContent().split("\\.");
				System.out.println("Printing Description- " + toInsert[0]);
				
				System.out.println("\n");
				//split the desctiption by fullstop
				
				
				//System.out.println(summary.item(i).getTextContent());
				
				//insertShit(source, titles.item(i).getTextContent(),summary.item(i).getTextContent());
				insertShit(source, titles.item(i).getTextContent(),toInsert[0]);
			}
			
			
		}
		catch (Exception e){
			System.out.println("heheheheheeee");
			System.out.println(e.getStackTrace());
			e.printStackTrace();
		}
		
		//read the reuters feed
	}
	
	private Document parseXML(InputStream stream) throws Exception {
		
		DocumentBuilderFactory objDocumentBuilderFactory = null;
		DocumentBuilder objDocumentBuilder = null;
		Document doc = null;
		try
		{
		    objDocumentBuilderFactory = DocumentBuilderFactory.newInstance();
		    objDocumentBuilder = objDocumentBuilderFactory.newDocumentBuilder();
	
		    doc = objDocumentBuilder.parse(stream);
		}
		catch(Exception ex)
		{
		    throw ex;
		}       
	
		return doc;
	 }
	 
	public void Connect() {
		try {
		    Class.forName(JDBC_DRIVER);
		    con = DriverManager.getConnection("jdbc:mysql://localhost/newsstream","root","");
		    statement= con.createStatement();
		    System.out.println ("Database connection established");
		    System.out.println("capturing from database...motthaaafaaacckaaaaa");
		}
		catch (Exception e) {
			System.out.println("heheheeee...we're f'd");
			System.out.println(e.getMessage());
		}
		
	}
	
	public void insertShit(String source, String headline, String description){
		
		try{
			
			String query = "INSERT INTO `news`(`source`, `headline`, `summary`) VALUES (?,?,?)";
			PreparedStatement ps = con.prepareStatement(query);
			ps.setString(1, source);
			ps.setString(2, headline);
			ps.setString(3, description);
			ps.executeUpdate(); 
		}
		catch (Exception e){
			System.out.println("ahh leaaaaveee it yeaaaaaa");
			System.out.println(e.getMessage());
		}
	}

}
