.PHONY: build-apphost run-aspire

build-apphost:
	@dotnet build ./Homunculy.AppHost/Homunculy.AppHost.csproj \
		-p:GenerateFullPaths=true \
		-p:Configuration=Debug \
		-p:Platform=AnyCPU

run-aspire:
	@dotnet run --project ./Homunculy.AppHost/Homunculy.AppHost.csproj