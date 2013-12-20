public class AttributeData {

    private int positive;
    private int negative;
    private int neutral;
    private String token;


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
        double pos_proportion = (positive / total_pos);
        double pos_ent = - pos_proportion * log2(pos_proportion);

        double neutral_proportion = (neutral / total_neut);
        double neut_ent = - neutral_proportion * log2(neutral_proportion);

        double negative_proportion = (negative / total_neg);
        double negative_ent = - negative_proportion * log2(negative_proportion);

        return pos_ent + neut_ent + negative_ent;
    }

    private double log2(double num) {
        return Math.log(num)/Math.log(2);
    }

    public String getToken() {
        return token;
    }
}
