public class AttributeData {

    private double positive;
    private double negative;
    private double neutral;
    private String token;
    private double entropy;


    AttributeData(String token) {
        this.token = token;
        positive = 0;
        negative = 0;
        neutral = 0;
    }

    public void addPositive() {
        positive++;
    }

    public void addNegative() {
        negative++;
    }

    public void addNeutral() {
        neutral++;
    }

    public double getEntropy(int total_pos, int total_neut, int total_neg) {
        double pos_ent;
        double neut_ent;
        double negative_ent;

        if(total_pos == 0) {
            System.out.println("Warning: Total number of positive instances was 0");
            pos_ent = 0;
        } else {
            double pos_proportion = (positive / total_pos);
            pos_ent = (pos_proportion*-1) * log2(pos_proportion);
        }

        if(total_neut == 0) {
            System.out.println("Warning: Total number of neutral instances was 0");
            neut_ent = 0;
        } else {
            double neutral_proportion = (neutral / total_neut);
            neut_ent = (neutral_proportion*-1) * log2(neutral_proportion);
        }

        if(total_neg == 0) {
            System.out.println("Warning: Total number of negative instances was 0");
            negative_ent = 0;
        } else {
            double negative_proportion = (negative / total_neg);
            negative_ent = (negative_proportion*-1) * log2(negative_proportion);
        }
        entropy = pos_ent + neut_ent + negative_ent;
        return pos_ent + neut_ent + negative_ent;
    }

    private double log2(double num) {
        if(num == 0) {
            return 0;
        }
        return Math.log(num)/Math.log(2);
    }

    public String getToken() {
        return token;
    }

    public String toString() {
        return "Token " + token + " Positive occurences " + positive + " Negative occurences " + negative + " Neutral occurences " + neutral + " with entropy of " + entropy;
    }
}
