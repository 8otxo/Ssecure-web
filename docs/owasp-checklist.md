# Checklist OWASP Top 10:2025 — Frontend / Lab

Completar semana a semana. Marcar: ✅ Cumple | ❌ Violado | ⏳ Pendiente

| ID | Categoría | Estado | Evidencia / Notas |
|----|-----------|--------|-------------------|
| A01 | Broken Access Control | ⏳ | |
| A02 | Security Misconfiguration | ❌ | Sin headers seguridad, CORS abierto |
| A03 | Software Supply Chain Failures | ⏳ | |
| A04 | Cryptographic Failures | ❌ | HTTP plano, contraseña en tránsito legible |
| A05 | Injection | ⏳ | |
| A06 | Insecure Design | ⏳ | |
| A07 | Authentication Failures | ❌ | Contraseña por defecto, cookie insegura |
| A08 | Software/Data Integrity Failures | ⏳ | |
| A09 | Logging and Alerting Failures | ⏳ | |
| A10 | Mishandling of Exceptional Conditions | ⏳ | |

## Clase 01 — notas iniciales

- Entorno deliberadamente vulnerable para demo MITM.
- Tests: `pytest tests/test_clase01_infra.py -v`
