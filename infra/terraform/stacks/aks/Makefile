.PHONY: help init fmt validate test workspace plan plan-noout apply apply-noout show destroy-plan destroy-apply clean

# Usage examples:
#   make plan ENV=prod
#   make apply ENV=prod
#   make plan ENV=dev
#
# Notes:
# - This stack uses Terraform Cloud/HCP Terraform backend (see backend.tf).
# - Using a saved plan (-out=tfplan) is recommended so apply uses the exact reviewed plan.

ENV ?= prod
TFVARS ?= ../../environments/$(ENV)/aks.tfvars
PLANFILE ?= tfplan.$(ENV)
DESTROYPLAN ?= tfdestroy.$(ENV)

# Workspace naming convention matches backend.tf docs.
TFC_WORKSPACE ?= homunculy-aks-$(ENV)

help:
	@echo "Targets: init fmt validate test workspace plan plan-noout apply apply-noout show destroy-plan destroy-apply clean"
	@echo "Defaults: ENV=$(ENV) TFVARS=$(TFVARS) TFC_WORKSPACE=$(TFC_WORKSPACE) PLANFILE=$(PLANFILE) DESTROYPLAN=$(DESTROYPLAN)"

init:
	terraform init

fmt:
	terraform fmt -recursive

validate:
	terraform validate

test:
	terraform test -verbose

workspace: init
	terraform workspace select $(TFC_WORKSPACE)

# Best practice: save the plan file then apply that exact plan.
plan: workspace
	terraform plan -var-file=$(TFVARS) -out=$(PLANFILE)

# Optional: show the plan contents (human readable) from the saved plan.
show:
	terraform show $(PLANFILE)

# Destroy workflow (best practice: create a saved destroy plan, then apply it)
destroy-plan: workspace
	terraform plan -destroy -var-file=$(TFVARS) -out=$(DESTROYPLAN)

destroy-apply: workspace
	terraform apply $(DESTROYPLAN)

apply: workspace
	terraform apply $(PLANFILE)

# Alternative: don't save a plan file (Terraform will re-calc on apply).
plan-noout: workspace
	terraform plan -var-file=$(TFVARS)

apply-noout: workspace
	terraform apply -var-file=$(TFVARS)

clean:
	@rm -f $(PLANFILE) $(DESTROYPLAN) tfplan tfplan.* tfdestroy.*