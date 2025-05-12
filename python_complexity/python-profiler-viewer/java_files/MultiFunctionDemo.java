import java.util.Random;
// import java.util.time;
import java.util.concurrent.TimeUnit;
public class MultiFunctionDemo {
    private static final Random random = new Random();

    public static void main(String[] args) {
        System.out.println("Starting program...");
        
        // Demonstrate different function calls
        processData();
        calculateResults();
        performComplexOperation();
        
        System.out.println("Program completed.");
    }

    private static void processData() {
        System.out.println("\nProcessing data...");
        int[] data = generateData(1000);
        analyzeData(data);
        filterData(data);
    }

    private static int[] generateData(int size) {
        System.out.println("Generating " + size + " random numbers...");
        int[] data = new int[size];
        for (int i = 0; i < size; i++) {
            data[i] = random.nextInt(1000);
        }
        return data;
    }

    private static void analyzeData(int[] data) {
        System.out.println("Analyzing data...");
        int sum = calculateSum(data);
        double avg = calculateAverage(data, sum);
        findMinMax(data);
        System.out.printf("Analysis results - Sum: %d, Avg: %.2f\n", sum, avg);
    }

    private static int calculateSum(int[] data) {
        int sum = 0;
        for (int value : data) {
            sum += value;
        }
        return sum;
    }

    private static double calculateAverage(int[] data, int sum) {
        return (double) sum / data.length;
    }

    private static void findMinMax(int[] data) {
        if (data.length == 0) return;
        
        int min = data[0];
        int max = data[0];
        
        for (int i = 1; i < data.length; i++) {
            if (data[i] < min) min = data[i];
            if (data[i] > max) max = data[i];
        }
        
        System.out.printf("Min: %d, Max: %d\n", min, max);
    }

    private static void filterData(int[] data) {
        int count = 0;
        for (int value : data) {
            if (value > 500) {
                count++;
            }
        }
        System.out.printf("Filtered %d elements > 500\n", count);
    }

    private static void calculateResults() {
        System.out.println("\nCalculating results...");
        for (int i = 0; i < 3; i++) {
            performCalculation(i);
        }
        recursiveFunction(3);
    }

    private static void performCalculation(int iteration) {
        long result = 0;
        for (int i = 0; i < 1000; i++) {
            result += i * iteration;
        }
        System.out.printf("Calculation %d result: %d\n", iteration, result);
    }

    private static void recursiveFunction(int depth) {
        System.out.println("Entering recursion depth: " + depth);
        // Thread.sleep(1);
        try{
        Thread.sleep(1000);}
        catch(Exception e){}
        if (depth > 0) {
            recursiveFunction(depth - 1);
        }
        System.out.println("Exiting recursion depth: " + depth);
    }

    private static void performComplexOperation() {
        System.out.println("\nPerforming complex operations...");
        matrixMultiplication();
        stringProcessing();
    }

    private static void matrixMultiplication() {
        System.out.println("Multiplying matrices...");
        int size = 5; // Smaller size for demonstration
        int[][] matrix1 = new int[size][size];
        int[][] matrix2 = new int[size][size];
        int[][] result = new int[size][size];
        
        // Initialize matrices with random values
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                matrix1[i][j] = random.nextInt(10);
                matrix2[i][j] = random.nextInt(10);
            }
        }
        
        // Multiply matrices
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                for (int k = 0; k < size; k++) {
                    result[i][j] += matrix1[i][k] * matrix2[k][j];
                }
            }
        }
        
        System.out.println("Matrix multiplication completed");
    }

    private static void stringProcessing() {
        System.out.println("Processing strings...");
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 100; i++) {
            sb.append(random.nextInt(1000)).append(" ");
        }
         try{
        Thread.sleep(1);}
        catch(Exception e){}
        System.out.println("Generated string with " + sb.toString().split(" ").length + " numbers");
    }
} 
