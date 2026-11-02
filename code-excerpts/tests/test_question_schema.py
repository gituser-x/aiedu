"""Independent tests for the public production normalization module."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'question-schema/generated_question_schema.py'
spec = importlib.util.spec_from_file_location('question_schema', path)
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)


class QuestionSchemaTests(unittest.TestCase):
    def test_dictionary_options(self):
        self.assertEqual(schema.normalize_options({'A':'甲', 'B':'乙'}),
                         [{'label':'A','text':'甲'}, {'label':'B','text':'乙'}])

    def test_string_and_rich_options(self):
        self.assertEqual(schema.normalize_options(['A. 甲', {'key':'B','content_markdown':'乙'}]),
                         [{'label':'A','text':'甲'}, {'label':'B','text':'乙'}])

    def test_top_level_options_survive(self):
        content = schema.normalize_generated_content({'stem':'请选择','options':{'A':'甲'},'answer':'A'})
        self.assertEqual(content['options'], [{'label':'A','text':'甲'}])

    def test_nested_content_wins(self):
        content = schema.normalize_generated_content({'stem':'旧题干','content':{'stem':'新题干'}})
        self.assertEqual(content['stem']['text'], '新题干')

    def test_answer_array(self):
        self.assertEqual(schema.normalize_generated_content({'answer':['A','C']})['answer'], 'A、C')

    def test_shared_material_kept_and_grouped(self):
        a = schema.normalize_generated_content({'stem':'问题一','shared_material':'原创示例材料'})
        b = schema.normalize_generated_content({'stem':'问题二','shared_material':'原创示例材料'})
        self.assertIn('原创示例材料', a['stem']['text'])
        self.assertEqual(a['extensions']['material_group'], b['extensions']['material_group'])

    def test_existing_material_not_duplicated(self):
        result = schema.normalize_generated_content({'stem':'材料：原创示例材料。问题？','shared_material':'原创示例材料'})
        self.assertEqual(result['stem']['text'].count('原创示例材料'), 1)

    def test_missing_options_are_not_invented(self):
        content = schema.normalize_generated_content({'stem':'一道待补充的题'})
        self.assertNotIn('options', content)
        self.assertFalse(content.get('answer'))

    def test_invalid_option_shape_is_empty(self):
        self.assertEqual(schema.normalize_options(None), [])


if __name__ == '__main__':
    unittest.main()
