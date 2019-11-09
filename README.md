# hw1

## Group members

Linxuan Xu

Hui Yang

## Explanation on the flags:
With `-emit-ast` flag on, the program will parse the input file into an AST tree in YAML format.

`-o` flag defines the place of output. In case where the output is not specified, the AST tree would be in standard output.

The last argv defines the place of input.

## How to Run
### Step 1: Install dependency packages
```
$ pip3 install -r requirements.txt 
```

### Step 2: Enter the directory that contains /bin/ekcc.py. Run the following line to check whether 
```
$ python3 ./bin/ekcc.py -emit-ast -o /path/to/output/file /path/to/input/file
```

For example:

case 1:
`
$ python3 ./bin/ekcc.py -emit-ast -o ./out/out.yml ./test_files/test1.ek
`

The command line is parsing ./test_files/test1.ek into an AST tree. The result would be in ./out/out.yml

case 2:
`
$ python3 ./bin/ekcc.py -emit-ast ./test_files/test1.ek
`

The command line is parsing ./test_files/test1.ek into an AST tree. The result would be in the standard output
