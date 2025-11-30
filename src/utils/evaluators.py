"""
Evaluadores para validar la calidad de las respuestas.
Usados principalmente por el Agente Crítico.
"""
from typing import Dict, List, Any
import re


class ResponseEvaluator:
    """Evaluador de calidad de respuestas."""
    
    @staticmethod
    def evaluate_coherence(response: str) -> Dict[str, Any]:
        """
        Evalúa la coherencia de la respuesta.
        Verifica estructura, longitud razonable y completitud de frases.
        """
        score = 1.0
        issues = []
        
        # Verificar longitud mínima
        if len(response.strip()) < 50:
            score -= 0.3
            issues.append("Respuesta demasiado corta")
        
        # Verificar que no esté vacía
        if not response.strip():
            score = 0.0
            issues.append("Respuesta vacía")
            return {"score": score, "issues": issues, "passed": False}
        
        # Verificar frases completas (termina con puntuación)
        if not response.strip()[-1] in '.!?':
            score -= 0.2
            issues.append("Respuesta no termina con puntuación adecuada")
        
        # Verificar estructura básica (al menos 2 oraciones)
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) < 2:
            score -= 0.1
            issues.append("Respuesta muy breve, considerar más detalle")
        
        return {
            "score": max(0.0, score),
            "issues": issues,
            "passed": score >= 0.6
        }
    
    @staticmethod
    def evaluate_context_alignment(response: str, context_docs: List[str]) -> Dict[str, Any]:
        """
        Evalúa si la respuesta está alineada con el contexto proporcionado.
        Verifica que mencione conceptos presentes en los documentos.
        """
        score = 1.0
        issues = []
        
        if not context_docs:
            return {
                "score": 0.0,
                "issues": ["No hay documentos de contexto"],
                "passed": False
            }
        
        # Extraer palabras clave del contexto
        context_text = " ".join(context_docs).lower()
        context_words = set(re.findall(r'\b\w{4,}\b', context_text))
        
        # Extraer palabras de la respuesta
        response_words = set(re.findall(r'\b\w{4,}\b', response.lower()))
        
        # Calcular overlap
        overlap = len(context_words & response_words)
        overlap_ratio = overlap / len(context_words) if context_words else 0
        
        if overlap_ratio < 0.1:
            score = 0.3
            issues.append("Muy poco overlap con el contexto proporcionado")
        elif overlap_ratio < 0.2:
            score = 0.6
            issues.append("Bajo overlap con el contexto")
        elif overlap_ratio < 0.3:
            score = 0.8
        
        return {
            "score": score,
            "overlap_ratio": overlap_ratio,
            "issues": issues,
            "passed": overlap_ratio >= 0.1
        }
    
    @staticmethod
    def detect_hallucinations(response: str, context_docs: List[str]) -> Dict[str, Any]:
        """
        Detecta posibles alucinaciones comparando la respuesta con el contexto.
        Identifica afirmaciones que no tienen soporte en los documentos.
        """
        issues = []
        hallucination_indicators = [
            "definitivamente",
            "sin duda",
            "está comprobado que",
            "todos los expertos",
            "nunca",
            "siempre",
            "absolutamente"
        ]
        
        response_lower = response.lower()
        context_text = " ".join(context_docs).lower()
        
        # Buscar indicadores de alucinación (afirmaciones categóricas)
        found_indicators = []
        for indicator in hallucination_indicators:
            if indicator in response_lower:
                found_indicators.append(indicator)
        
        if found_indicators:
            issues.append(f"Posibles afirmaciones categóricas no respaldadas: {', '.join(found_indicators)}")
        
        # Extraer números/estadísticas de la respuesta
        numbers_in_response = re.findall(r'\b\d+(?:\.\d+)?%?\b', response)
        numbers_in_context = re.findall(r'\b\d+(?:\.\d+)?%?\b', context_text)
        
        unsupported_numbers = [n for n in numbers_in_response if n not in numbers_in_context]
        if unsupported_numbers:
            issues.append(f"Números/estadísticas no encontrados en contexto: {', '.join(unsupported_numbers)}")
        
        # Score basado en issues encontrados
        score = 1.0 - (len(issues) * 0.3)
        score = max(0.0, score)
        
        return {
            "score": score,
            "issues": issues,
            "passed": score >= 0.7,
            "indicators_found": found_indicators
        }
    
    @staticmethod
    def evaluate_completeness(response: str, query: str) -> Dict[str, Any]:
        """
        Evalúa si la respuesta aborda completamente la consulta.
        """
        score = 1.0
        issues = []
        
        # Extraer palabras clave de la consulta
        query_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
        response_words = set(re.findall(r'\b\w{4,}\b', response.lower()))
        
        # Verificar que la respuesta mencione temas de la consulta
        overlap = len(query_words & response_words)
        coverage = overlap / len(query_words) if query_words else 0
        
        if coverage < 0.3:
            score = 0.4
            issues.append("La respuesta no aborda suficientemente la consulta")
        elif coverage < 0.5:
            score = 0.7
            issues.append("La respuesta aborda parcialmente la consulta")
        
        # Verificar presencia de estructura (si es resumen o comparación)
        if "resumen" in query.lower() or "resume" in query.lower():
            if len(response.split('\n')) < 3:
                score -= 0.2
                issues.append("Resumen carece de estructura clara")
        
        if "compar" in query.lower():
            if "diferencia" not in response.lower() and "similar" not in response.lower():
                score -= 0.3
                issues.append("Comparación no menciona diferencias/similitudes explícitamente")
        
        return {
            "score": max(0.0, score),
            "coverage": coverage,
            "issues": issues,
            "passed": score >= 0.6
        }
    
    @staticmethod
    def evaluate_citations(response: str, has_citations: bool) -> Dict[str, Any]:
        """
        Evalúa la presencia y calidad de las citas.
        """
        score = 1.0
        issues = []
        
        # Buscar patrones de citación
        citation_patterns = [
            r'\[(\d+)\]',           # [1], [2]
            r'\(doc\s*\d+\)',       # (doc 1)
            r'\(fuente:.*?\)',      # (fuente: nombre)
            r'según\s+\w+',         # según documento
            r'de acuerdo con',      # de acuerdo con
        ]
        
        found_citations = False
        for pattern in citation_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                found_citations = True
                break
        
        if has_citations and not found_citations:
            score = 0.5
            issues.append("Se esperaban citas pero no se encontraron")
        
        return {
            "score": score,
            "has_citations": found_citations,
            "issues": issues,
            "passed": not has_citations or found_citations
        }
    
    @classmethod
    def evaluate_full(cls, response: str, query: str, context_docs: List[str], 
                      has_citations: bool = True) -> Dict[str, Any]:
        """
        Evaluación completa de la respuesta.
        Combina todas las métricas.
        """
        coherence = cls.evaluate_coherence(response)
        alignment = cls.evaluate_context_alignment(response, context_docs)
        hallucinations = cls.detect_hallucinations(response, context_docs)
        completeness = cls.evaluate_completeness(response, query)
        citations = cls.evaluate_citations(response, has_citations)
        
        # Score general (promedio ponderado)
        overall_score = (
            coherence["score"] * 0.25 +
            alignment["score"] * 0.25 +
            hallucinations["score"] * 0.25 +
            completeness["score"] * 0.20 +
            citations["score"] * 0.05
        )
        
        # Compilar todos los issues
        all_issues = (
            coherence["issues"] +
            alignment["issues"] +
            hallucinations["issues"] +
            completeness["issues"] +
            citations["issues"]
        )
        
        # Determinar si pasa la validación
        passed = (
            coherence["passed"] and
            alignment["passed"] and
            hallucinations["passed"] and
            completeness["passed"] and
            citations["passed"]
        )
        
        return {
            "overall_score": overall_score,
            "passed": passed,
            "criteria": {
                "coherence": coherence,
                "context_alignment": alignment,
                "hallucinations": hallucinations,
                "completeness": completeness,
                "citations": citations
            },
            "all_issues": all_issues,
            "recommendation": "accept" if passed else "regenerate"
        }
