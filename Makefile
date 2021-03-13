.PHONY: plan

deploy:
	cdktf synth
	cd cdktf.out/ && terraform apply

plan:
	cdktf synth
	cd cdktf.out/ && terraform plan

init:
	cdktf synth
	cd cdktf.out/ && terraform init

opa:
	cdktf synth
	cd cdktf.out/ && terraform plan --out tfplan.binary && terraform show -json tfplan.binary > tfplan.json
	
