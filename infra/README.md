# Infrastructure

Terraform will create only the minimal Phase 1 development environment:

- one synthetic `orders-api` Lambda;
- its CloudWatch log group and one error alarm;
- the least-privilege roles needed by the application and read-only diagnostic tools;
- a scoped S3 location for the synthetic runbook.

No EKS, Kubernetes, OpenShift, GitOps, production resources, or real operational data are in the active scope.
