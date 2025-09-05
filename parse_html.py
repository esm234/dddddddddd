#!/usr/bin/env python3
"""
HTML Results Parser
يستخرج الأسئلة والإجابات الصحيحة من HTML صفحة النتائج
"""

import json
import argparse
import sys
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup


class HTMLResultsParser:
    def __init__(self):
        self.questions: List[Dict[str, Any]] = []
        self.current_passage: str = ""
    
    def parse_html_file(self, html_file_path: str, category: str) -> List[Dict[str, Any]]:
        """Parse HTML file and extract questions with correct answers"""
        try:
            print(f"Reading HTML file: {html_file_path}")
            
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return self.parse_html_content(html_content, category)
            
        except Exception as e:
            print(f"Error reading HTML file: {e}")
            return []
    
    def parse_html_content_from_string(self, html_content: str, category: str) -> List[Dict[str, Any]]:
        """Parse HTML content from string (for bot usage)"""
        try:
            return self.parse_html_content(html_content, category)
        except Exception as e:
            print(f"Error parsing HTML content: {e}")
            return []
    
    def parse_html_content(self, html_content: str, category: str) -> List[Dict[str, Any]]:
        """Parse HTML content and extract questions with correct answers"""
        try:
            # Clear previous questions for each new file
            self.questions = []
            self.current_passage = ""
            
            soup = BeautifulSoup(html_content, 'html5lib')
            
            # Extract form title
            form_title = self.extract_form_title(soup)
            print(f"Form title: {form_title}")
            
            # Find all question containers
            question_containers = soup.find_all('div', class_='Qr7Oae', role='listitem')
            
            if not question_containers:
                print("No question containers found. Trying alternative selectors...")
                # Try alternative selectors
                question_containers = soup.find_all('div', role='listitem')
            
            if not question_containers:
                print("Error: No question containers found")
                return []
            
            print(f"Found {len(question_containers)} question containers")
            
            # Extract questions
            question_number = 1
            passage_found = False
            
            for i, container in enumerate(question_containers):
                try:
                    # Check if this is a passage (for reading comprehension)
                    if category == "استيعاب المقروء" and not passage_found:
                        passage_text = self.extract_passage_text(container)
                        if passage_text:
                            self.current_passage = passage_text
                            passage_found = True
                            print(f"Found passage: {passage_text[:100]}...")
                            continue
                    
                    # Extract question data
                    question_data = self.extract_question_from_container(container, question_number, category)
                    if question_data:
                        # Additional validation for reading comprehension
                        if category == "استيعاب المقروء":
                            # Ensure question is related to the passage
                            if not self.is_question_related_to_passage(question_data['question']):
                                print(f"Skipping unrelated question: {question_data['question'][:50]}...")
                                continue
                        
                        question_data["exam"] = form_title
                        question_data["category"] = category
                        if category == "استيعاب المقروء" and self.current_passage:
                            question_data["passage"] = self.current_passage
                        self.questions.append(question_data)
                        print(f"Question {question_number}: {question_data['question']} -> Answer: {question_data['answer']}")
                        question_number += 1
                except Exception as e:
                    print(f"Error extracting question {question_number}: {e}")
                    continue
            
            print(f"Total questions extracted: {len(self.questions)}")
            return self.questions
            
        except Exception as e:
            print(f"Error parsing HTML content: {e}")
            return self.questions
    
    def extract_form_title(self, soup) -> str:
        """Extract form title from soup"""
        try:
            # Try multiple selectors for form title
            selectors = [
                'h1',
                '[role="heading"]',
                '.freebirdFormviewerViewHeaderTitle',
                '.M7eMe'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text().strip()
                    if title and len(title) > 5:  # Reasonable title length
                        return title
            
            # Fallback: look for any heading with Arabic text
            headings = soup.find_all(['h1', 'h2', 'h3'], role='heading')
            for heading in headings:
                text = heading.get_text().strip()
                if any('\u0600' <= char <= '\u06FF' for char in text):  # Arabic characters
                    return text
                    
        except Exception as e:
            print(f"Warning: Could not extract form title: {e}")
        
        return ""
    
    def extract_passage_text(self, container) -> str:
        """Extract passage text for reading comprehension"""
        try:
            # Look for text that appears to be a passage (longer text without choices)
            text_element = container.select_one('.M7eMe')
            if text_element:
                text = text_element.get_text().strip()
                
                # Enhanced validation for passage text
                if self.is_valid_passage(text, container):
                    return text
            
            # Try alternative selectors for passage text
            alternative_selectors = [
                '.freebirdFormviewerViewItemsItemItemTitle',
                '.freebirdFormviewerViewItemsItemItemDescription',
                'div[role="heading"] + div',
                '.M7eMe span'
            ]
            
            for selector in alternative_selectors:
                element = container.select_one(selector)
                if element:
                    text = element.get_text().strip()
                    if self.is_valid_passage(text, container):
                        return text
            
            return ""
        except Exception as e:
            print(f"Error extracting passage text: {e}")
            return ""
    
    def is_valid_passage(self, text: str, container) -> bool:
        """Validate if text is a proper passage for reading comprehension"""
        try:
            # Basic length check
            if len(text) < 30:
                return False
            
            # Check if container has radiogroup (indicates it's a question, not passage)
            if container.select_one('[role="radiogroup"]'):
                return False
            
            # Check for question indicators that suggest this is not a passage
            question_indicators = [
                "؟", "?", "اختر", "أي", "ما", "متى", "أين", "كيف", "لماذا",
                "أكمل", "ضع", "حدد", "اذكر", "اشرح", "قارن", "وضح"
            ]
            
            # If text starts with question indicators, it's likely a question
            for indicator in question_indicators:
                if text.strip().startswith(indicator):
                    return False
            
            # Check for multiple sentences (passages usually have multiple sentences)
            sentence_count = text.count('.') + text.count('؟') + text.count('!')
            if sentence_count < 2:
                return False
            
            # Check for Arabic text content (most passages are in Arabic)
            arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
            if arabic_chars < len(text) * 0.3:  # At least 30% Arabic characters
                return False
            
            # Check if text contains common passage patterns
            passage_patterns = [
                "في النص", "من النص", "النص يتحدث", "يذكر النص", "وفقاً للنص",
                "بناءً على النص", "من خلال النص", "النص يشير", "النص يوضح"
            ]
            
            # If text contains passage patterns, it's likely a question about a passage
            for pattern in passage_patterns:
                if pattern in text:
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error validating passage: {e}")
            return False
    
    def extract_question_from_container(self, container, question_number: int, category: str) -> Optional[Dict[str, Any]]:
        """Extract question data from a single container"""
        try:
            # Extract question text
            question_text = self.extract_question_text(container)
            if not question_text:
                return None
            
            # Skip non-question fields (student name, password, test title)
            skip_questions = [
                "اسم الطالب",
                "كلمة المرور",
                "الاختبار",
                "اسم الطالب :",
                "كلمة المرور:",
                "الاختبار :"
            ]
            
            if question_text.strip() in skip_questions:
                print(f"Skipping non-question field: {question_text}")
                return None
            
            # Extract all choices
            choices = self.extract_choices(container)
            
            # Find correct answer
            correct_answer = self.find_correct_answer(container)
            
            question_data = {
                "question_number": question_number,
                "question": question_text,
                "type": "اختيار",
                "choices": choices,
                "answer": correct_answer,
                "exam": "",
                "category": category
            }
            
            # Add passage for reading comprehension
            if category == "استيعاب المقروء" and self.current_passage:
                question_data["passage"] = self.current_passage
            
            return question_data
            
        except Exception as e:
            print(f"Error extracting question from container: {e}")
            return None
    
    def extract_question_text(self, container) -> str:
        """Extract question text from container"""
        try:
            # Look for question text in .M7eMe span
            question_element = container.select_one('.M7eMe')
            if question_element:
                text = question_element.get_text().strip()
                if text and self.is_valid_question_text(text):
                    return text
            
            # Fallback: look for any heading
            heading = container.select_one('[role="heading"]')
            if heading:
                text = heading.get_text().strip()
                if text and self.is_valid_question_text(text):
                    return text
            
            # Try alternative selectors
            alternative_selectors = [
                '.freebirdFormviewerViewItemsItemItemTitle',
                '.freebirdFormviewerViewItemsItemItemDescription',
                'div[role="heading"] + div .M7eMe'
            ]
            
            for selector in alternative_selectors:
                element = container.select_one(selector)
                if element:
                    text = element.get_text().strip()
                    if text and self.is_valid_question_text(text):
                        return text
            
            return ""
            
        except Exception as e:
            print(f"Error extracting question text: {e}")
            return ""
    
    def is_valid_question_text(self, text: str) -> bool:
        """Validate if text is a proper question"""
        try:
            # Basic length check
            if len(text) < 5:
                return False
            
            # Skip non-question fields (student name, password, test title)
            skip_questions = [
                "اسم الطالب", "كلمة المرور", "الاختبار", "اسم الطالب :", 
                "كلمة المرور:", "الاختبار :", "النتيجة", "الدرجة",
                "التاريخ", "الوقت", "المدة", "المرحلة", "الصف"
            ]
            
            for skip_text in skip_questions:
                if skip_text in text:
                    return False
            
            # Check for question indicators
            question_indicators = [
                "؟", "?", "اختر", "أي", "ما", "متى", "أين", "كيف", "لماذا",
                "أكمل", "ضع", "حدد", "اذكر", "اشرح", "قارن", "وضح",
                "في النص", "من النص", "النص يتحدث", "يذكر النص", "وفقاً للنص"
            ]
            
            # Check if text contains question indicators
            for indicator in question_indicators:
                if indicator in text:
                    return True
            
            # Check for Arabic text content
            arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
            if arabic_chars < len(text) * 0.5:  # At least 50% Arabic characters
                return False
            
            # If text is long and doesn't contain question indicators, it might be a passage
            if len(text) > 100 and not any(indicator in text for indicator in question_indicators):
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating question text: {e}")
            return False
    
    def is_question_related_to_passage(self, question_text: str) -> bool:
        """Check if question is related to reading comprehension passage"""
        try:
            # Check for reading comprehension question patterns
            passage_question_patterns = [
                "في النص", "من النص", "النص يتحدث", "يذكر النص", "وفقاً للنص",
                "بناءً على النص", "من خلال النص", "النص يشير", "النص يوضح",
                "النص يدل", "النص يعبر", "النص يصف", "النص يبين", "النص يوضح",
                "ما المقصود", "ما المعنى", "ما المقصود بـ", "ما معنى",
                "أي مما يلي", "أي من", "أي مما يأتي", "أي من الآتي"
            ]
            
            # Check if question contains passage-related patterns
            for pattern in passage_question_patterns:
                if pattern in question_text:
                    return True
            
            # Check for question words that indicate reading comprehension
            question_words = ["ما", "أي", "متى", "أين", "كيف", "لماذا", "من"]
            if any(word in question_text for word in question_words):
                return True
            
            # If question is very short and doesn't contain passage patterns, it might not be related
            if len(question_text) < 20 and not any(pattern in question_text for pattern in passage_question_patterns):
                return False
            
            return True
            
        except Exception as e:
            print(f"Error checking question relation to passage: {e}")
            return True  # Default to True to avoid skipping valid questions
    
    def extract_choices(self, container) -> List[str]:
        """Extract all choices from container"""
        choices = []
        try:
            # Find radiogroup
            radiogroup = container.select_one('[role="radiogroup"]')
            if radiogroup:
                # Get all choice labels
                choice_labels = radiogroup.find_all('label')
                for label in choice_labels:
                    # Get the choice text from .aDTYNe span
                    choice_span = label.select_one('.aDTYNe')
                    if choice_span:
                        choice_text = choice_span.get_text().strip()
                        if choice_text and choice_text not in choices:
                            choices.append(choice_text)
            
            return choices
            
        except Exception as e:
            print(f"Error extracting choices: {e}")
            return []
    
    def find_correct_answer(self, container) -> str:
        """Find the correct answer from container"""
        try:
            # First, look for "الإجابة الصحيحة" section (for wrong answers)
            correct_section = container.select_one('.D42QGf')
            if correct_section:
                # Find the correct answer label
                correct_label = correct_section.select_one('label')
                if correct_label:
                    # Get the choice text from .aDTYNe span
                    choice_span = correct_label.select_one('.aDTYNe')
                    if choice_span:
                        return choice_span.get_text().strip()
            
            # Look for labels that contain "إجابة صحيحة" text
            # This handles the case where the correct answer is marked within the choice
            all_labels = container.find_all('label')
            for label in all_labels:
                label_text = label.get_text()
                if "إجابة صحيحة" in label_text:
                    # Extract the choice text from this label
                    choice_span = label.select_one('.aDTYNe')
                    if choice_span:
                        return choice_span.get_text().strip()
            
            # Look for div with class "H6Scae" that contains "إجابة صحيحة"
            # This is another way the correct answer might be marked
            correct_divs = container.find_all('div', class_='H6Scae')
            for div in correct_divs:
                if "إجابة صحيحة" in div.get_text():
                    # Find the parent label
                    parent_label = div.find_parent('label')
                    if parent_label:
                        choice_span = parent_label.select_one('.aDTYNe')
                        if choice_span:
                            return choice_span.get_text().strip()
            
            return ""
            
        except Exception as e:
            print(f"Error finding correct answer: {e}")
            return ""


def main():
    try:
        # Display category options
        categories = {
            "1": "التناظر اللفظي",
            "2": "إكمال الجمل", 
            "3": "استيعاب المقروء",
            "4": "الخطأ السياقي",
            "5": "المفردة الشاذة"
        }
        
        print("="*50)
        print("أهلاً بك في أداة استخراج الأسئلة من HTML")
        print("="*50)
        print("اختر نوع القسم:")
        for key, value in categories.items():
            print(f"{key}. {value}")
        print("="*50)
        
        # Get category choice from user
        while True:
            choice = input("أدخل رقم القسم (1-5): ").strip()
            if choice in categories:
                category = categories[choice]
                break
            else:
                print("خطأ: الرقم غير صحيح. يرجى اختيار رقم من 1 إلى 5")
        
        print(f"تم اختيار: {category}")
        
        # Get HTML file path from user
        html_file = input("أدخل اسم ملف HTML: ").strip()
        if not html_file:
            print("خطأ: يجب إدخال اسم ملف HTML")
            sys.exit(1)
        
        # Get output file path from user
        output_file = input("أدخل اسم ملف الإخراج (JSON): ").strip()
        if not output_file:
            print("خطأ: يجب إدخال اسم ملف الإخراج")
            sys.exit(1)
        
        # Add .json extension if not provided
        if not output_file.endswith('.json'):
            output_file += '.json'
        
        html_parser = HTMLResultsParser()
        questions = html_parser.parse_html_file(html_file, category)
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        
        print(f"تم حفظ النتائج في {output_file}")
        print(f"إجمالي الأسئلة: {len(questions)}")
        
        # Print to stdout as well
        print("\n" + "="*50)
        print("الأسئلة المستخرجة:")
        print("="*50)
        print(json.dumps(questions, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"خطأ: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
