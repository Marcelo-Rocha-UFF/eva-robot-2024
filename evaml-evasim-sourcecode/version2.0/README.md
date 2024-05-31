# **EvaML** (**eva_parser**)

This folder contains the *parser* of the EvaML language. After processing the *parser* over a script, a new XML file is generated and can be imported into the simulator. The *parser* must be executed on the command line as in the following example.

```
> python3 eva_parser.py script.xml -c
```

If there is an error in the code, *parser* will indicate the error and stop the parsing process. The name of the generated file will be the name defined in the *name* attribute within the XML script.

In this same directory you will also find the **evaml-schema** folder which contains the **xml-schema** file with the definitions of the elements of the EvaML language. For a new element to be added to the EvaML language, it must be defined within the **xsd** file.