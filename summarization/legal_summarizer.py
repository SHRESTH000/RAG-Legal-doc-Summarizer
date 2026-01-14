"""
Legal Text Summarization Module
Supports multiple LLM backends (OpenAI, HuggingFace, LLaMA)
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    """Result from summarization"""
    summary: str
    case_summary: str
    key_issues: List[str]
    legal_analysis: str
    relevant_sections: List[str]
    judgment: str
    key_entities: Dict[str, List[str]]
    metadata: Dict[str, Any]


class LegalSummarizer:
    """
    Legal text summarizer with support for multiple LLM backends
    Following base paper approach with compression ratio constraint (0.05 to 0.5)
    """
    
    def __init__(self,
                 model_type: str = "openai",  # "openai", "huggingface", "llama", "ollama", "mistral_api"
                 model_name: str = "gpt-4",
                 max_length: int = 512,
                 compression_ratio: float = 0.2,  # 0.05 to 0.5 as per base paper
                 temperature: float = 0.3,
                 ollama_base_url: Optional[str] = None,
                 mistral_api_key: Optional[str] = None):
        """
        Initialize legal summarizer
        
        Args:
            model_type: Type of LLM backend
            model_name: Model name/identifier
            max_length: Maximum summary length
            compression_ratio: Target compression ratio (0.05 to 0.5)
            temperature: Generation temperature
        """
        self.model_type = model_type
        self.model_name = model_name
        self.max_length = max_length
        self.compression_ratio = max(0.05, min(0.5, compression_ratio))
        self.temperature = temperature
        self.ollama_base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.mistral_api_key = mistral_api_key or os.getenv("MISTRAL_API_KEY", "")
        
        self.llm = None
        self._initialize_model()
        
        logger.info(f"Legal Summarizer initialized: {model_type}/{model_name}, "
                   f"compression_ratio={compression_ratio}")
    
    def _initialize_model(self):
        """Initialize the LLM model based on type"""
        if self.model_type == "openai":
            try:
                # Try new API format first
                try:
                    from openai import OpenAI
                    self.llm = OpenAI()
                    self._use_new_api = True
                    logger.info("OpenAI client initialized (new API)")
                except ImportError:
                    # Fallback to old API
                    import openai
                    self.llm = openai
                    self._use_new_api = False
                    logger.info("OpenAI client initialized (old API)")
            except ImportError:
                logger.warning("OpenAI not installed. Install with: pip install openai")
                self.llm = None
        
        elif self.model_type == "huggingface":
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
                self.llm = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device_map="auto" if self._has_gpu() else None
                )
                logger.info(f"HuggingFace model {self.model_name} loaded")
            except ImportError:
                logger.warning("Transformers not installed. Install with: pip install transformers")
                self.llm = None
            except Exception as e:
                logger.error(f"Error loading HuggingFace model: {e}")
                self.llm = None
        
        elif self.model_type == "llama":
            # For LLaMA models (requires llama.cpp or similar)
            try:
                from llama_cpp import Llama
                self.llm = Llama(model_path=self.model_name)
                logger.info(f"LLaMA model loaded from {self.model_name}")
            except ImportError:
                logger.warning("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
                self.llm = None
            except Exception as e:
                logger.error(f"Error loading LLaMA model: {e}")
                self.llm = None
        
        elif self.model_type == "ollama":
            # For Ollama local models
            try:
                import requests
                self.requests = requests
                
                # Test connection
                try:
                    response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                    if response.status_code == 200:
                        models = response.json().get('models', [])
                        model_names = [m.get('name', '') for m in models]
                        logger.info(f"Ollama connected at {self.ollama_base_url}")
                        logger.info(f"Available models: {model_names}")
                        
                        # Check if specified model exists
                        if self.model_name:
                            # Try exact match first
                            if self.model_name not in model_names:
                                # Try partial match (e.g., "mistral" matches "mistral:latest")
                                matched = [m for m in model_names if self.model_name in m or m.startswith(self.model_name)]
                                if matched:
                                    self.model_name = matched[0]
                                    logger.info(f"Matched model: {self.model_name}")
                                else:
                                    logger.warning(f"Model '{self.model_name}' not found. Available: {model_names}")
                                    if model_names:
                                        logger.info(f"Using first available model: {model_names[0]}")
                                        self.model_name = model_names[0]
                            else:
                                logger.info(f"Using specified model: {self.model_name}")
                        elif model_names:
                            # No model specified, use first available
                            self.model_name = model_names[0]
                            logger.info(f"No model specified, using: {self.model_name}")
                        
                        self.llm = True  # Mark as initialized
                    else:
                        logger.warning(f"Ollama connection failed: {response.status_code}")
                        self.llm = None
                except Exception as e:
                    logger.warning(f"Could not connect to Ollama at {self.ollama_base_url}: {e}")
                    logger.info("Make sure Ollama is running: ollama serve")
                    self.llm = None
            except ImportError:
                logger.warning("requests not installed. Install with: pip install requests")
                self.llm = None
        
        elif self.model_type == "mistral_api":
            # For Mistral AI API (hosted)
            try:
                from mistralai import Mistral
                
                if not self.mistral_api_key:
                    raise ValueError("Mistral API key required. Set MISTRAL_API_KEY environment variable or pass mistral_api_key parameter.")
                
                self.llm = Mistral(api_key=self.mistral_api_key)
                
                # Test connection by listing models
                try:
                    models = self.llm.models.list()
                    logger.info(f"Mistral API connected. Available models: {[m.id for m in models.data[:5]]}")
                except Exception as e:
                    logger.warning(f"Mistral API connection test failed: {e}")
                
                # Set default model if not specified
                if not self.model_name or self.model_name == "gpt-4":
                    self.model_name = "mistral-medium-latest"  # Default Mistral model
                    logger.info(f"Using default Mistral model: {self.model_name}")
                
            except ImportError:
                logger.warning("mistralai not installed. Install with: pip install mistralai")
                self.llm = None
            except Exception as e:
                logger.error(f"Error initializing Mistral API: {e}")
                self.llm = None
        
        else:
            logger.warning(f"Unknown model type: {self.model_type}")
            self.llm = None
    
    def _has_gpu(self) -> bool:
        """Check if GPU is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _create_legal_prompt(self, context: str, original_text: str = "") -> str:
        """Create prompt for legal summarization"""
        prompt = f"""You are an expert legal analyst specializing in Indian criminal law. 
Your task is to create a comprehensive summary of the following criminal judgment.

Context Information:
{context}

Instructions:
1. Provide a concise summary of the case facts (2-3 sentences)
2. Identify key legal issues and arguments (bullet points)
3. Summarize the court's reasoning and decision (2-3 paragraphs)
4. List all relevant legal sections cited (IPC, CrPC, Evidence Act)
5. Extract key entities: parties, judges, dates, case numbers
6. Highlight the final judgment/order

Format your response as follows:

Case Summary: [2-3 sentence summary of facts]

Key Issues:
- [Issue 1]
- [Issue 2]
- [Issue 3]

Legal Analysis: [2-3 paragraphs explaining court's reasoning]

Relevant Sections: 
- IPC Section XXX
- CrPC Section XXX
- Evidence Act Section XXX

Judgment: [Final decision and order]

Key Entities:
- Parties: [list]
- Judges: [list]
- Case Number: [case number]
- Date: [date]
- Court: [court name]

Ensure accuracy and legal correctness. Cite specific sections and precedents mentioned.
Maintain factual consistency with the provided context.
"""
        return prompt
    
    def summarize(self, 
                  context: str,
                  original_text: Optional[str] = None,
                  metadata: Optional[Dict] = None) -> SummaryResult:
        """
        Generate summary from context
        
        Args:
            context: Assembled context from RAG system
            original_text: Original judgment text (optional)
            metadata: Judgment metadata (optional)
            
        Returns:
            SummaryResult with structured summary
        """
        if not self.llm:
            raise ValueError("LLM not initialized. Check model configuration.")
        
        # Create prompt
        prompt = self._create_legal_prompt(context, original_text or "")
        
        # Generate summary
        summary_text = self._generate_summary(prompt)
        
        # Parse structured output
        parsed = self._parse_summary(summary_text)
        
        return SummaryResult(
            summary=summary_text,
            case_summary=parsed.get('case_summary', ''),
            key_issues=parsed.get('key_issues', []),
            legal_analysis=parsed.get('legal_analysis', ''),
            relevant_sections=parsed.get('relevant_sections', []),
            judgment=parsed.get('judgment', ''),
            key_entities=parsed.get('key_entities', {}),
            metadata=metadata or {}
        )
    
    def _generate_summary(self, prompt: str) -> str:
        """Generate summary using the configured LLM"""
        if self.model_type == "openai":
            return self._generate_openai(prompt)
        elif self.model_type == "huggingface":
            return self._generate_huggingface(prompt)
        elif self.model_type == "llama":
            return self._generate_llama(prompt)
        elif self.model_type == "ollama":
            return self._generate_ollama(prompt)
        elif self.model_type == "mistral_api":
            return self._generate_mistral_api(prompt)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def _generate_openai(self, prompt: str) -> str:
        """Generate using OpenAI API"""
        try:
            if hasattr(self, '_use_new_api') and self._use_new_api:
                # New API format (openai >= 1.0.0)
                response = self.llm.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are an expert legal analyst specializing in Indian criminal law."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.max_length,
                    temperature=self.temperature
                )
                return response.choices[0].message.content
            else:
                # Old API format (openai < 1.0.0)
                response = self.llm.ChatCompletion.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are an expert legal analyst specializing in Indian criminal law."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.max_length,
                    temperature=self.temperature
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    def _generate_huggingface(self, prompt: str) -> str:
        """Generate using HuggingFace transformers"""
        try:
            result = self.llm(
                prompt,
                max_length=self.max_length,
                temperature=self.temperature,
                do_sample=True,
                top_p=0.9,
                truncation=True
            )
            return result[0]['generated_text'][len(prompt):].strip()
        except Exception as e:
            logger.error(f"HuggingFace generation error: {e}")
            raise
    
    def _generate_llama(self, prompt: str) -> str:
        """Generate using LLaMA"""
        try:
            result = self.llm(
                prompt,
                max_tokens=self.max_length,
                temperature=self.temperature,
                top_p=0.9,
                echo=False
            )
            return result['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"LLaMA generation error: {e}")
            raise
    
    def _generate_ollama(self, prompt: str) -> str:
        """Generate using Ollama API"""
        try:
            # Prepare request
            url = f"{self.ollama_base_url}/api/generate"
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_length,  # max tokens
                    "top_p": 0.9
                }
            }
            
            # Make request
            response = self.requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get('response', '').strip()
            
            return generated_text
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    def _generate_mistral_api(self, prompt: str) -> str:
        """Generate using Mistral AI API"""
        try:
            response = self.llm.chat.complete(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert legal analyst specializing in Indian criminal law."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_length,
                temperature=self.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Mistral API generation error: {e}")
            raise
    
    def _parse_summary(self, summary_text: str) -> Dict:
        """Parse structured summary from LLM output"""
        parsed = {
            'case_summary': '',
            'key_issues': [],
            'legal_analysis': '',
            'relevant_sections': [],
            'judgment': '',
            'key_entities': {}
        }
        
        lines = summary_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if line.startswith('Case Summary:'):
                current_section = 'case_summary'
                parsed['case_summary'] = line.replace('Case Summary:', '').strip()
            elif line.startswith('Key Issues:'):
                current_section = 'key_issues'
            elif line.startswith('Legal Analysis:'):
                current_section = 'legal_analysis'
                parsed['legal_analysis'] = line.replace('Legal Analysis:', '').strip()
            elif line.startswith('Relevant Sections:'):
                current_section = 'relevant_sections'
            elif line.startswith('Judgment:'):
                current_section = 'judgment'
                parsed['judgment'] = line.replace('Judgment:', '').strip()
            elif line.startswith('Key Entities:'):
                current_section = 'key_entities'
            elif current_section:
                # Add content to current section
                if current_section == 'key_issues':
                    if line.startswith('-'):
                        parsed['key_issues'].append(line[1:].strip())
                elif current_section == 'relevant_sections':
                    if line.startswith('-'):
                        parsed['relevant_sections'].append(line[1:].strip())
                elif current_section == 'legal_analysis':
                    parsed['legal_analysis'] += ' ' + line
                elif current_section == 'judgment':
                    parsed['judgment'] += ' ' + line
                elif current_section == 'case_summary':
                    parsed['case_summary'] += ' ' + line
        
        return parsed
    
    def calculate_compression_ratio(self, original_text: str, summary: str) -> float:
        """Calculate compression ratio"""
        if not original_text:
            return 0.0
        return len(summary) / len(original_text)


def create_summarizer(model_type: str = "openai",
                     model_name: str = "gpt-4",
                     compression_ratio: float = 0.2) -> LegalSummarizer:
    """Factory function to create summarizer"""
    return LegalSummarizer(
        model_type=model_type,
        model_name=model_name,
        compression_ratio=compression_ratio
    )
