//
// Sourced from http://www.jayway.com/2012/04/07/continuous-deployment-versioning-and-git/


import java.net.URL;
import java.util.jar.Manifest;
import java.util.jar.Attributes;
import java.lang.RuntimeException;

public class VersionReader {

    private static final Attributes attr;

    static {
        String className = VersionReader.class.getSimpleName() + ".class";
        String classPath = VersionReader.class.getResource(className).toString();
        if (!classPath.startsWith("jar")) {
            throw new RuntimeException("VersionReader: not contained within a JAR");
        }
        String manifestPath = classPath.substring(0, classPath.lastIndexOf("!") + 1) +
    "/META-INF/MANIFEST.MF";
        Manifest mf = null;
        try {
            mf = new Manifest(new URL(manifestPath).openStream());
        }
        catch (Exception e) {
            throw new RuntimeException("Error opening manifest", e);
        }
        attr = mf.getMainAttributes();
    }


    private VersionReader() {}

    public static String getGitSha1() {
        return attr.getValue("git-SHA-1");
    }
}
