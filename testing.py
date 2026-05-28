# =========================================================
# IMPORT REQUIRED MODULES
# =========================================================
 
import unittest      # Built-in testing framework
import ast           # Used to convert Python code into AST (needed for parsing)
import os            # File path handling
import tempfile      # Create temporary files/folders for testing
 
# Import functions from your main script
from code_graph_insert import (
    get_python_files,
    extract_imports,
    extract_functions,
    extract_cypher_queries,
    get_query_type,
    extract_node_labels,
    extract_relationship_labels,
    create_query_id,
    process_file,
    get_connection,
    create_code_graph_schema
)
 
# =========================================================
# TEST CLASS
# =========================================================
 
class TestCodeGraphFunctions(unittest.TestCase):
 
    # -----------------------------------------------------
    # ✅ Test 1: get_python_files()
    # Purpose:
    # Check if only .py files are detected (ignores others)
    # -----------------------------------------------------
    def test_get_python_files(self):
 
        with tempfile.TemporaryDirectory() as temp_dir:
 
            py_file = os.path.join(temp_dir, "test.py")
            txt_file = os.path.join(temp_dir, "notes.txt")
 
            open(py_file, "w").close()
            open(txt_file, "w").close()
 
            result = get_python_files(temp_dir)
 
            # Should return only one Python file
            self.assertEqual(len(result), 1)
            self.assertTrue(result[0].endswith("test.py"))
 
    # -----------------------------------------------------
    # ✅ Test 2: extract_imports()
    # Purpose:
    # Verify imports are correctly extracted from AST
    # -----------------------------------------------------
    def test_extract_imports(self):
 
        code = """
import os
import sys
from math import sqrt
"""
 
        tree = ast.parse(code)
 
        result = extract_imports(tree)
 
        self.assertIn("os", result)
        self.assertIn("sys", result)
        self.assertIn("math", result)
 
    # -----------------------------------------------------
    # ✅ Test 3: extract_functions()
    # Purpose:
    # Ensure all functions in code are identified correctly
    # -----------------------------------------------------
    def test_extract_functions(self):
 
        code = """
def add(a,b): return a+b
def greet(): return "hi"
"""
 
        tree = ast.parse(code)
 
        result = extract_functions(tree, "sample.py")
 
        self.assertEqual(len(result), 2)
 
        names = [f["name"] for f in result]
 
        self.assertIn("add", names)
        self.assertIn("greet", names)
 
    # -----------------------------------------------------
    # ✅ Test 4 (NEW): extract_cypher_queries()
    # Purpose:
    # Check if Cypher queries inside conn.execute() are detected
    # -----------------------------------------------------
    def test_extract_cypher_queries(self):
 
        code = '''
conn.execute("MATCH (n:Person) RETURN n")
conn.execute("CREATE (n:Employee)")
'''
        tree = ast.parse(code)
 
        result = extract_cypher_queries(tree)
 
        self.assertEqual(len(result), 2)
        self.assertIn("MATCH (n:Person) RETURN n", result)
 
    # -----------------------------------------------------
    # ✅ Test 5 (NEW): get_query_type()
    # Purpose:
    # Validate classification of query types
    # -----------------------------------------------------
    def test_get_query_type(self):
 
        self.assertEqual(get_query_type("CREATE NODE TABLE Person"), "CREATE_NODE_TABLE")
        self.assertEqual(get_query_type("CREATE REL TABLE KNOWS"), "CREATE_REL_TABLE")
        self.assertEqual(get_query_type("MERGE (n)"), "MERGE_DATA")
        self.assertEqual(get_query_type("MATCH (n) RETURN n"), "MATCH_QUERY")
        self.assertEqual(get_query_type("UNKNOWN"), "OTHER")
 
    # -----------------------------------------------------
    # ✅ Test 6 (NEW): extract_node_labels()
    # Purpose:
    # Extract node labels from Cypher queries
    # -----------------------------------------------------
    def test_extract_node_labels(self):
 
        query = "MATCH (n:Person)"
 
        labels = extract_node_labels(query)
 
        self.assertIn("Person", labels)
 
    # -----------------------------------------------------
    # ✅ Test 7 (NEW): extract_relationship_labels()
    # Purpose:
    # Extract relationship labels from queries
    # -----------------------------------------------------
    def test_extract_relationship_labels(self):
 
        query = "MATCH (a)-[:WORKS_AT]->(b)"
 
        labels = extract_relationship_labels(query)
 
        self.assertIn("WORKS_AT", labels)
 
    # -----------------------------------------------------
    # ✅ Test 8 (NEW): create_query_id()
    # Purpose:
    # Ensure same query → same ID (consistency)
    # -----------------------------------------------------
    def test_create_query_id(self):
 
        id1 = create_query_id("file.py", "MATCH (n)")
        id2 = create_query_id("file.py", "MATCH (n)")
 
        self.assertEqual(id1, id2)
 
    # -----------------------------------------------------
    # ✅ Test 9 (IMPORTANT INTEGRATION TEST)
    # Purpose:
    # Test FULL pipeline:
    # File → parsing → DB insertion
    # -----------------------------------------------------
    def test_process_file_integration(self):
 
        with tempfile.TemporaryDirectory() as temp_dir:
 
            file_path = os.path.join(temp_dir, "sample.py")
 
            with open(file_path, "w") as f:
                f.write("""
import os
 
def test():
    return 1
 
conn.execute("MATCH (n:Person) RETURN n")
""")
 
            conn = get_connection()
 
            create_code_graph_schema(conn)
 
            process_file(conn, file_path)
 
            # Verify something got inserted into DB
            result = conn.execute("MATCH (f:PyFile) RETURN f.path").fetchall()
 
            self.assertTrue(len(result) > 0)
 
    # -----------------------------------------------------
    # ✅ Test 10 (EDGE CASE)
    # Purpose:
    # Ensure invalid Python file does not crash the system
    # -----------------------------------------------------
    def test_invalid_python_file(self):
 
        with tempfile.TemporaryDirectory() as temp_dir:
 
            bad_file = os.path.join(temp_dir, "bad.py")
 
            with open(bad_file, "w") as f:
                f.write("def broken(:")   # Invalid syntax
 
            conn = get_connection()
 
            # Should NOT throw exception
            process_file(conn, bad_file)
 
 
# =========================================================
# RUN TESTS
# =========================================================
 
if __name__ == "__main__":
    unittest.main()
 
