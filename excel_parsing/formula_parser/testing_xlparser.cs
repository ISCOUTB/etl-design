using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using XLParser;

class Program
{
    static bool isValidFunctionName(string functionName)
    {
        return string.IsNullOrEmpty(functionName)
            // || !functionName.All(char.IsLetter)
            || functionName.Length < 2;
    }

    static void Main(string[] args)
    {
        string excel_formula = "SUM(A1:A10) + AVERAGE(B1:B10) + 10 + SUM(C1, 1) + (B1 + B2)";
        XLParser.FormulaAnalyzer parser = new XLParser.FormulaAnalyzer(excel_formula);

        // Print root
        System.Console.WriteLine(parser.Root);
        System.Console.WriteLine();

        // Print all functions
        System.Console.WriteLine("Functions:");
        foreach (var item in parser.Functions())
        {
            System.Console.WriteLine(item);
        }

        // Print all numbers
        System.Console.WriteLine("\nNumbers:");
        foreach (var item in parser.Numbers())
        {
            System.Console.WriteLine(item);
        }

        // Print all constants
        System.Console.WriteLine("\nConstants:");
        foreach (var item in parser.Constants())
        {
            System.Console.WriteLine(item);
        }

        // Print Parse Tree
        System.Console.WriteLine("\nParse Tree:");
        System.Console.WriteLine(XLParser.ExcelFormulaParser.Print(parser.Root));

        // Print all ParserReferences
        System.Console.WriteLine("\nReferences:");
        foreach (var item in parser.References())
        {
            System.Console.WriteLine(XLParser.ExcelFormulaParser.Print(item));
        }

        // Get all nodes
        System.Console.WriteLine("\n\n\nAll Nodes:");
        var allNodes = parser.Root.AllNodes().ToList(); // parser.AllNodes;
        var functions = allNodes.Where(node => node.IsFunction());
        foreach (var function in functions) // ParseTreeNode
        {
            string functionName = function.GetFunction();
            if (functionName == ":" || !isValidFunctionName(functionName))
            {
                continue;
            }

            System.Console.WriteLine($"Function: {functionName}");

            var subFunctions = function.AllNodes().ToList().Where(node => node.IsFunction());
            if (subFunctions.Count() == 0)
            {
                System.Console.WriteLine("  No sub-functions found.");
            }
            System.Console.WriteLine($"SubFunction - References:");
            foreach (var subFunction in subFunctions)
            {
                string subFunctionName = subFunction.GetFunction();
                if (isValidFunctionName(subFunctionName) && subFunctions.Count() > 1)
                {
                    continue;
                } // Skip range operator

                var references = subFunction.GetReferenceNodes();
                var numbers = subFunction
                    .AllNodesConditional(ExcelFormulaParser.IsNumberWithSign)
                    .Where(node => node.Is(GrammarNames.Number) || node.IsNumberWithSign())
                    .Select(node =>
                        double.Parse(node.Print(), NumberStyles.Float, CultureInfo.InvariantCulture)
                    );
                System.Console.WriteLine($"  SubFunction: {subFunctionName}");
                System.Console.WriteLine($"  Numbers: {string.Join(", ", numbers)}");
                foreach (var reference in references)
                {
                    System.Console.WriteLine(
                        $"  References: {XLParser.ExcelFormulaParser.Print(reference)}"
                    );
                }
                System.Console.WriteLine();
            }
            System.Console.WriteLine();
        }
    }
}


/*
System.Console.WriteLine("\n\n\nAll Nodes:");
        var allNodes = parser.Root.AllNodes().ToList(); // parser.AllNodes;
        var functions = allNodes.Where(node => node.IsFunction());
        foreach (var function in functions) // ParseTreeNode
        {
            string functionName = function.GetFunction();
            if (isValidFunctionName(functionName))
            {
                continue; // Skip invalid function names
            }

            System.Console.WriteLine($"Function: {functionName}");
            var references = function.GetReferenceNodes();
            var numbers = function
                .AllNodesConditional(XLParser.ExcelFormulaParser.IsNumberWithSign)
                .Where(node => node.Is(GrammarNames.Number) || node.IsNumberWithSign())
                .Select(node =>
                    double.Parse(node.Print(), NumberStyles.Float, CultureInfo.InvariantCulture)
                );

            foreach (var reference in references)
            {
                System.Console.WriteLine(
                    $"  References: {XLParser.ExcelFormulaParser.Print(reference)}\n  Numbers: {string.Join(", ", numbers)}"
                );
            }
        }
        System.Console.WriteLine();
*/
