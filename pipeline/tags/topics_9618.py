"""Topic keyword tables for CAIE 9618 Computer Science.

Topics are the syllabus *sections* (1-20). Unlike the maths syllabuses the
section number does not encode the paper, so the mapping is explicit:

  Paper 1 Theory Fundamentals                        -> sections 1-8
  Paper 2 Problem-solving and Programming Skills     -> sections 9-12
  Paper 3 Advanced Theory                            -> sections 13-20
  Paper 4 Practical                                  -> sections 19-20
"""

TOPICS = {
"1":  ("Information representation", {
    3: ["binary", "hexadecimal", "denary", "two's complement", "bcd", "ascii", "unicode",
        "bitmap", "vector graphic", "sample rate", "compression", "lossless", "lossy"],
    2: ["bit depth", "resolution", "colour depth", "file size", "run-length"],
    1: ["character set", "image"]}),
"2":  ("Communication", {
    3: ["lan", "wan", "network topology", "client-server", "peer-to-peer", "wifi",
        "bit streaming", "cloud computing", "router", "ip address"],
    2: ["bandwidth", "transmission", "serial", "parallel", "simplex", "duplex", "network"],
    1: ["internet", "url"]}),
"3":  ("Hardware", {
    3: ["logic gate", "logic circuit", "truth table", "nand", "nor", "xor",
        "karnaugh", "sum-of-products", "boolean algebra", "flip-flop"],
    2: ["input device", "output device", "primary storage", "secondary storage",
        "ram", "rom", "monitor", "printer"],
    1: ["hardware", "circuit"]}),
"4":  ("Processor Fundamentals", {
    3: ["von neumann", "fetch-execute", "accumulator", "program counter",
        "memory address register", "assembly language", "opcode", "operand",
        "addressing mode", "interrupt", "bit manipulation"],
    2: ["cpu", "register", "bus", "instruction set", "clock speed", "cache", "core"],
    1: ["processor"]}),
"5":  ("System Software", {
    3: ["operating system", "compiler", "interpreter", "assembler", "language translator",
        "memory management", "scheduling", "utility software"],
    2: ["source code", "object code", "bootstrap", "device driver", "kernel"],
    1: ["software"]}),
"6":  ("Security, privacy and data integrity", {
    3: ["malware", "phishing", "pharming", "firewall", "authentication", "data integrity",
        "validation", "verification", "checksum", "parity", "backup"],
    2: ["password", "biometric", "access rights", "encryption", "virus", "hacking"],
    1: ["security", "privacy"]}),
"7":  ("Ethics and Ownership", {
    3: ["copyright", "software licence", "ethical", "professional ethics", "code of conduct",
        "open source", "freeware", "shareware", "acm", "ieee"],
    2: ["ownership", "intellectual property", "licence", "piracy"],
    1: ["ethics"]}),
"8":  ("Databases", {
    3: ["relational database", "primary key", "foreign key", "normalisation", "1nf", "2nf", "3nf",
        "sql", "select", "dbms", "entity-relationship", "referential integrity"],
    2: ["table", "record", "field", "query", "index", "attribute", "tuple"],
    1: ["database"]}),

"9":  ("Algorithm Design and Problem-solving", {
    3: ["abstraction", "decomposition", "flowchart", "linear search",
        "binary search", "bubble sort", "insertion sort", "trace table",
        "complete the table", "dry run", "purpose of the algorithm"],
    2: ["algorithm", "pseudocode", "stepwise refinement", "identify the purpose",
        "sequence of steps", "logic error", "output of the algorithm"],
    1: ["logic", "problem"]}),
"10": ("Data Types and Structures", {
    3: ["record", "array", "1d array", "2d array", "file organisation",
        "serial file", "sequential file", "random file", "abstract data type",
        "linked list", "stack", "queue", "binary tree", "hash"],
    2: ["declare", "data type", "integer", "string", "boolean", "index of the array",
        "openfile", "readfile", "writefile"],
    1: ["structure"]}),
"11": ("Programming", {
    3: ["byref", "byval", "local variable", "global variable", "scope of",
        "case of", "repeat until", "for to next", "while do",
        "structured programming", "nested loop"],
    2: ["procedure", "parameter", "iteration", "selection", "definite loop",
        "indefinite loop", "write program code"],
    1: ["function", "declare", "assignment", "loop", "condition", "return",
        "call", "variable", "statement"]}),
"12": ("Software Development", {
    3: ["program development life cycle", "waterfall", "iterative model", "rapid application",
        "test data", "normal data", "abnormal data", "boundary data",
        "white-box", "black-box", "corrective maintenance", "adaptive", "perfective"],
    2: ["testing", "debugging", "maintenance", "design", "analysis", "breakpoint",
        "stepping", "walkthrough", "structure chart", "state-transition"],
    1: ["development"]}),

"13": ("Data Representation (A2)", {
    3: ["user-defined data type", "non-composite", "composite", "enumerated", "pointer",
        "floating-point", "mantissa", "exponent", "normalised form", "underflow", "overflow"],
    2: ["record type", "set", "class", "binary floating"],
    1: ["representation"]}),
"14": ("Communication and internet", {
    3: ["protocol", "tcp/ip", "http", "ftp", "smtp", "pop3", "imap", "packet switching",
        "circuit switching", "osi", "domain name", "dns"],
    2: ["layer", "handshake", "port", "socket", "ipv4", "ipv6"],
    1: ["protocol stack"]}),
"15": ("Hardware, Virtual Machines and Boolean Algebra", {
    3: ["parallel processing", "virtual machine", "simd", "misd", "mimd", "sisd",
        "massively parallel", "risc", "cisc", "pipelining", "interrupt handling",
        "karnaugh", "k-map", "boolean algebra", "de morgan", "sum-of-products",
        "logic circuit", "truth table", "flip-flop", "half adder", "full adder"],
    2: ["multi-core", "co-processor", "register file", "throughput",
        "nand", "nor", "xor", "logic gate", "simplify the expression"],
    1: ["architecture", "circuit"]}),
"16": ("System Software (A2)", {
    3: ["purposes of an operating system", "process states", "scheduler", "paging",
        "segmentation", "virtual memory", "thrashing", "disk thrashing",
        "translation software", "lexical analysis", "syntax analysis", "reverse polish",
        "syntax diagram", "backus", "bnf", "code generation", "optimisation"],
    2: ["multitasking", "kernel", "memory management unit", "page table", "swap",
        "interpreter", "compiler", "assembler", "symbol table"],
    1: ["operating system"]}),
"17": ("Security (A2)", {
    3: ["symmetric encryption", "asymmetric encryption", "public key", "private key",
        "digital signature", "digital certificate", "ssl", "tls", "quantum cryptography",
        "certificate authority"],
    2: ["encryption", "cipher", "key exchange", "hash", "plaintext", "ciphertext"],
    1: ["secure"]}),
"18": ("Artificial Intelligence", {
    3: ["artificial intelligence", "machine learning", "neural network", "deep learning",
        "supervised learning", "unsupervised learning", "reinforcement learning",
        "expert system", "graph traversal", "a* algorithm", "dijkstra"],
    2: ["training data", "back propagation", "hidden layer", "inference engine",
        "knowledge base", "heuristic"],
    1: ["intelligent"]}),
"19": ("Computational thinking and problem solving", {
    3: ["recursion", "recursive", "stack frame", "binary tree", "in-order",
        "pre-order", "post-order", "quick sort", "merge sort", "insertion sort",
        "big o", "time complexity", "space complexity",
        "linked list", "stack", "queue", "abstract data type", "circular queue",
        "push", "pop", "enqueue", "dequeue", "head pointer", "tail pointer"],
    2: ["pointer", "node", "search algorithm", "sorting algorithm", "bubble sort",
        "next pointer", "free list", "traverse"],
    1: ["algorithm", "efficiency"]}),
"20": ("Further Programming", {
    3: ["programming paradigm", "object-oriented", "declarative programming",
        "low-level programming", "inheritance", "polymorphism", "encapsulation",
        "getter", "setter", "constructor", "class definition", "prolog",
        "instantiat", "superclass", "subclass", "inherits"],
    2: ["file handling", "exception", "openfile", "readfile", "writefile",
        "closefile", "paradigm"],
    1: ["object", "class", "method", "attribute", "instance", "private", "public"]}),
}

COMPONENT_TOPICS = {
    "1": ["1", "2", "3", "4", "5", "6", "7", "8"],
    "2": ["9", "10", "11", "12"],
    "3": ["13", "14", "15", "16", "17", "18", "19", "20"],
    "4": ["19", "20"],
}

COMPONENT_NAME = {
    "1": "Theory Fundamentals",
    "2": "Fundamental Problem-solving and Programming Skills",
    "3": "Advanced Theory",
    "4": "Practical",
}

PAPER_TOTAL = {"1": 75, "2": 75, "3": 75, "4": 75}
