# Infrastructure

Terraform creates only the minimal Phase 1 development environment:

- one synthetic `orders-api` Lambda;
- its seven-day CloudWatch log group and one error-pattern alarm;
- an execution role that can write only to that Lambda's log stream.

The alarm has **no actions**. It cannot send a notification, invoke a function, or change a resource. The first application deployment is healthy by default. A human can deliberately set `inject_missing_config=true` in a reviewed Terraform run to reproduce the one documented development-only failure.

## Commands, in order

Run these from this directory. `init`, `fmt`, `validate`, and `plan` do not create AWS resources. Review the plan before deciding whether to apply it.

```powershell
terraform init
terraform fmt -check
terraform validate
terraform plan
```

Do not run `terraform apply` until you understand the plan and are ready to create the small development-only environment. When the project is no longer needed, `terraform destroy` is the normal cleanup path.

No EKS, Kubernetes, OpenShift, GitOps, production resources, real operational data, Bedrock deployment, or diagnostic-agent permissions are in this infrastructure checkpoint.
