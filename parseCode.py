code = """class Solution {
	public static int findSmallestElement(int[] nums, int n){
		int smallest = nums[0];
	
		for (int i=0; i<n; i++) {
			if (nums[i] < smallest){
				smallest = nums[i];
            }
        }
	
		return smallest;
    }
}"""

print(code.replace("\t", "\\t").replace("    ", "\\t").replace("\n", "\\n"))