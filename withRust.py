import timeit
from cffi import FFI
ffi = FFI()
lib = ffi.dlopen("short_long/target/release/short_long.dll")
ffi.cdef("""
    double short_long(const char *, uint64_t);
"""
)

#LOAD STRING
example = ""

with open("formalSentences.txt",encoding="utf8") as f:
    for line in f:
        example += line

#PRINT RESULT
print("With Rust: ")
string = example.encode()
cstr = ffi.new("char[]", string)
print(str(int(lib.short_long(cstr,len(cstr)) * 100)) + "%")



#TIMEIT
the_code = """
string = example.encode()
cstr = ffi.new("char[]", string)
lib.short_long(cstr,len(cstr))
"""

print("Elapsed time: {:.5f}s".format(sum(timeit.repeat(the_code, globals=globals(),repeat=20,number=1))/20))