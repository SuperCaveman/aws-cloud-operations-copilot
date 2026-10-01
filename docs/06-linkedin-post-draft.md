# LinkedIn post draft — publish after the Phase 1 demo is complete

> I built a small AWS Cloud Operations Copilot to learn the operational side of AI agents.
>
> The project investigates one synthetic Lambda incident: a missing non-secret development setting in an `orders-api` service. It reads a scoped CloudWatch alarm, bounded error logs, safe Lambda metadata, and a private S3 runbook. A LangGraph workflow checks the evidence first; Amazon Bedrock produces a short explanation only when the evidence supports an active incident.
>
> The important design choice was what the agent **cannot** do: it cannot read secrets, choose arbitrary AWS resources, run write APIs, or remediate anything. The engineer still reviews and makes any change through the normal deployment process.
>
> I deployed the development lab with Terraform and tested both the failure signal and recovery path in AWS. I also added a guard for stale alerts, so a service updated after an error is reported as possibly recovering instead of prompting a duplicate change.
>
> This gave me practical reps with AWS Lambda, CloudWatch, S3, IAM least privilege, Terraform, LangGraph, and Bedrock—applied to an operations workflow rather than a chatbot demo.

## Publish checklist

- Finish the Streamlit interface and record a short, sanitized demo.
- Confirm all statements still match the repository and deployment evidence.
- Add sanitized Lambda and CloudWatch screenshots; obscure account identifiers.
- Link the public GitHub repository.
- Do not say the copilot is production-ready, autonomous, Kubernetes-based, or able to fix AWS resources.
