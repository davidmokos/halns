## GOLang Planner Wrapper

### Build and use from Python

The following command creates a shared library that can be used from other languages
```bash
go build -buildmode=c-shared -o golang_impl.so
```

or create library for specific OS and arch
```bash
GOOS=linux GOARCH=amd64 go build -buildmode=c-shared -o golang_impl.so
```