public class DelayFunctions {

    public static void main(String[] args) {
        System.out.println("Starting...");

        functionOne();
        functionTwo();
        functionThree();
        functionFour();

        System.out.println("All functions completed.");
    }

    public static void functionOne() {
        System.out.println("Function One started.");
        sleepThreeSeconds();
        System.out.println("Function One completed.");
    }

    public static void functionTwo() {
        System.out.println("Function Two started.");
        sleepThreeSeconds();
        System.out.println("Function Two completed.");
    }

    public static void functionThree() {
        System.out.println("Function Three started.");
        sleepThreeSeconds();
        System.out.println("Function Three completed.");
    }

    public static void functionFour() {
        System.out.println("Function Four started.");
        sleepThreeSeconds();
        System.out.println("Function Four completed.");
    }

    private static void sleepThreeSeconds() {
        try {
            Thread.sleep(3000); // 3000 milliseconds = 3 seconds
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt(); // restore the interrupt status
            System.out.println("Sleep was interrupted");
        }
    }
}
