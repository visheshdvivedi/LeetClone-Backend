import json
from typing import List

import requests
from traceback import format_exc
from string import Template

from .models import Problem, FieldType

PYTHON_DEFAULT_CODE_BOILERPLATE = """class Solution:
    def ${func_name}(self, ${func_params}):
        # write your code here
"""

JAVASCRIPT_DEFAULT_CODE_BOILERPLATE = """function ${func_name}(${func_params}) {
    // write your code here
}
"""

JAVA_DEFAULT_CODE_BOILERPLATE = """class Solution {
    public static ${func_return_type} ${func_name}(${func_params}) {
        //write your code here
    }
}
"""

PYTHON_BOILERPLATE = """
from typing import List

${source_code}

${read_inputs}

sol = Solution()
print(sol.${func_name}(${args}), end='')
"""

JAVASCRIPT_BOILERPLATE = """
${source_code}

${read_inputs}

let val = ${func_name}(${args});
console.log(val);
"""

JAVA_BOILERPLATE = """
${source_code}

class Main{

    public static void printIntArray(int[] out){
        
        System.out.print("[");
        for (int i=0; i<out.length; i++){
            if (i == 0)
                System.out.print(out[i]);
            else
                System.out.print(", " + out[i]);
        }
        System.out.print("]");
        
    }

    public static void printStringArray(String[] out){
        
        System.out.print("[");
        for (int i=0; i<out.length; i++){
            if (i == 0)
                System.out.print(out[i]);
            else
                System.out.print(", " + out[i]);
        }
        System.out.print("]");
        
    }

    public static void main(String args[]){
        ${read_inputs}

        Solution sol = new Solution();
        ${out_type} output = sol.${func_name}(${args});
        ${out_print}
    }
}
"""

def find(func, list):
    for element in list:
        if func(element):
            return element

class JudgeManager:
    def __init__(self):
        self.url = "http://4.240.75.170"

    @staticmethod
    def create_default_code(name: str, inputs: List[dict]) -> dict:
        languages = ['python', 'java', 'javascript']
        output = {}
        for language in languages:
            code = JudgeManager.create_default_code_by_language(name, language, inputs)
            output[language] = code
        return output

    @staticmethod
    def create_default_code_by_language(name: str, language: str, inputs: List[dict]) -> str:

        print(name, language, inputs)

        if language == "python":
            func_name = name.replace(" ", "")
            func_name = func_name[0].lower() + func_name[1:]

            func_params = ", ".join([input.name for input in inputs if input.name != "output"])
            return Template(PYTHON_DEFAULT_CODE_BOILERPLATE).substitute(func_name=func_name, func_params=func_params)
        elif language == "javascript":
            func_name = name.replace(" ", "")
            func_name = func_name[0].lower() + func_name[1:]

            func_params = ", ".join([input.name for input in inputs if input.name != "output"])
            return Template(JAVASCRIPT_DEFAULT_CODE_BOILERPLATE).substitute(func_name=func_name, func_params=func_params)
        elif language == "java":
            func_name = name.replace(" ", "")
            func_name = func_name[0].lower() + func_name[1:]

            func_params = []
            func_return_type = ""

            for input in inputs:
                if input.name == "output":
                    if input.type == FieldType.INT:
                        func_return_type = "int"
                    elif input.type == FieldType.STRING:
                        func_return_type = "string"
                    elif input.type == FieldType.ARRAY_INT:
                        func_return_type = "int[]"
                    elif input.type == FieldType.ARRAY_STR:
                        func_return_type = "string[]"
                    continue

                if input.type == FieldType.INT:
                    func_params.append(f"int {input.name}")
                elif input.type == FieldType.STRING:
                    func_params.append(f"string {input.name}")
                elif input.type == FieldType.ARRAY_INT:
                    func_params.append(f"int[] {input.name}")
                elif input.type == FieldType.ARRAY_STR:
                    func_params.append(f"string[] {input.name}")

            func_params = ", ".join(func_params)
            return Template(JAVA_DEFAULT_CODE_BOILERPLATE).substitute(func_name=func_name, func_return_type=func_return_type, func_params=func_params)

    def run(self, code, language, stdin):
        try:

            code.replace()
            response = requests.post(
                self.url + "/submissions?wait=true",
                data={
                    "source_code": code,
                    "language_id": language,
                    "stdin": stdin
                }
            )
            if not response.ok:
                return False, response.content
            
            data = response.json()
            for index in range(data['submissions']):
                data['submissions'][index]['stdout'] = self.parse_stdout(data['submissions'][index]['stdout'])
            return True, data

        except Exception as ex:
            return False, ex
        
    def create_batch(self, codes, language):
        try:

            # extra code to remove '\\n' and '\\t' from code
            for i in range(len(codes)):
                codes[i] = codes[i].replace("\\n", "\n").replace("\\t", "\t")

            body = {"submissions": [
                { 
                    "source_code": codes[iter],
                    "language_id": language
                } for iter in range(len(codes))
            ]}
        
            response = requests.post(
                self.url + "/submissions/batch",
                json = body
            )

            if not response.ok:
                return False, response
            
            return True, response.json()

        except Exception as ex:
            return False, format_exc()
        
    def get_batch(self, tokens):
        try:
            response = requests.get(
                self.url + "/submissions/batch?tokens=" + ",".join(tokens)
            )

            if not response.ok:
                return False, response.content
            
            return True, response.json()

        except Exception as ex:
            return False, ex
        
    def create_boilerplate_code(self, source_code: str, problem, language, is_sample = True) -> str:
        """
        Combines the source code, problem details, the selected language  type to create a final boilerplate code for the solution

        Args:
            source_code (str): predefined source code
            problem (Problem): model problem object
            language (Language): model language object
            is_sample (bool, optional): whether the test case is sample test case or not. Defaults to True.

        Returns:
            string: boilerplate code
        """

        codes = []
        testcases = []

        if is_sample:
            testcases = problem.testcases.filter(is_sample=True).all()
        else:
            testcases = problem.testcases.all()


        for testcase in testcases:

            code = ""
            inputs = testcase.inputs.all()
            args = []
            
            func_name = problem.name.replace(" ", "")
            func_name = func_name[0].lower() + func_name[1:]

            read_inputs = ""
            out_type = ""
            out_print = ""

            for input in inputs:
                if input.name == "output":
                    if input.type == 1:
                        out_type = "int"
                        out_print = "System.out.print(output);"
                    elif input.type == 2:
                        out_type = "String"
                        out_print = "System.out.print(output);"
                    elif input.type == 3:
                        out_type = "int[]"
                        out_print = "Main.printIntArray(output);"
                    elif input.type == 4:
                        out_type = "int[]"
                        out_print = "Main.printStringArray(output);"
                    continue

                args.append(input.name)

                if language.name == "python":
                    read_inputs += f"{input.name} = {input.value}\n"

                elif language.name == "javascript":
                    read_inputs += f"let {input.name} = {input.value};\n"

                elif language.name == "java":
                    if input.type == 1:
                        read_inputs += f"int {input.name} = {input.value};\n"
                    elif input.type == 2:
                        read_inputs += f"String {input.name} = {input.value};\n"
                    elif input.type == 3:
                        read_inputs += f"int[] {input.name} = new int[] "+"{ "+ input.value.replace("[", "").replace("]", "") +" };\n"
                    elif input.type == 4:
                        read_inputs += f"String[] {input.name} = new String[] "+"{ "+ input.value.replace("[", "").replace("]", "") +" };\n"

                elif language.name == "csharp":
                    if input.type == 1:
                        read_inputs += f"int {input.name} = {input.value};\n"
                    elif input.type == 2:
                        read_inputs += f"string {input.name} = {input.value};\n"
                    elif input.type == 3:
                        read_inputs += f"int[] {input.name} = new int[] "+"{ "+ input.value.replace("[", "").replace("]", "") +" };\n"
                    elif input.type == 4:
                        read_inputs += f"string[] {input.name} = new string[] "+"{ "+ input.value.replace("[", "").replace("]", "") +" };\n"
            
            if language.name == "python":
                code = Template(PYTHON_BOILERPLATE).substitute(args=",".join(args), func_name=func_name, read_inputs=read_inputs, source_code=source_code)
            elif language.name == "javascript":    
                code = Template(JAVASCRIPT_BOILERPLATE).substitute(args=",".join(args), func_name=func_name, read_inputs=read_inputs, source_code=source_code)
            elif language.name == "java":
                code = Template(JAVA_BOILERPLATE).substitute(args=",".join(args), func_name=func_name, read_inputs=read_inputs, source_code=source_code, out_type=out_type, out_print=out_print)

            codes.append(code)
        
        return codes

    def parse_stdout(self, out):
        """
        Parse the standard output to remove all unnecessary characters

        Args:
            out (string): standard output

        Returns:
            str: parsed standard output
        """
        if out == None:
            return out

        if "[ " in out and " ]" in out:
            out = out.replace("[ ", "[").replace(" ]", "]")
        if "\n" in out:
            out = out.replace("\n", "")
        return out
    
    def get_submission_status(self, testcases, submissions):
        """
        Get the status of submission (whether all answers match testcase results or not)

        Args:
            testcases (List[TestCase]): List of testcases within the problem
            submissions (List[]): List of Judge0 submission

        Returns:
            bool: True if all answers are correct else False
        """
        for index, testcase in enumerate(testcases):
            original_output = find(lambda x: x.name == "output", testcase.inputs.all()).value
            expected_output = submissions[index]['stdout']

            if original_output != expected_output:
                return False
            
        return True