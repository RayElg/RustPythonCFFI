# [Speed up Python using Rust and CFFI](https://raynorelgie.com/md/#!RustPythonCFFI.md)

## Python is slow.
Python is a language that lends itself to fast development, but slow programs.


Python is dynamically typed, so the developer doesn’t have to be explicit about data types and datatype conversion. Python is interpreted, which allows easy debugging and faster compile times. Both of these things trade CPU time for ease of development. Since a CPU cycle happens in a fraction of a second, and humans need to be fed and housed, this will generally be a good trade-off.

This principle falls apart when the running time of a program is measured in minutes rather than seconds, or the program is run thousands of times. The great deal of overhead that Python incurs by being easy to develop becomes a source of frustration and wasted resources.

## Enter rust.
Designed by Mozilla Research employee Graydon Hoare, Rust is a statically typed language designed for both memory safety and speed.

It restricts the developer in many ways that ensure the developed program is as error-free and performant as possible. These restrictions, while not allowing the developer to ignore as many “under the hood” operations as in Python, helps Rust to have one of the fastest language implementations available.

#The Problem
Let’s suppose we’re undertaking a data science project where we analyze Wikipedia articles. One of our scripts should be able to take in a string extracted from Wikipedia, and return the fraction of the words that are longer than 8 characters, ignoring “the” and “a”.

```python
import timeit
def shortLong(string):
    split = string.split()
    split = [i for i in split if (i != "the") & (i != "a")]
    l = 0
    for i in split:
        if len(i) > 8:
            l += 1
    return l / len(split)
```


We’ll take a 1MB sample file to use as a test string for this new method, to make sure we don’t run into any errors, and see how long it takes.

```python
import timeit
def shortLong(string):
    split = string.split()
    l = 0
    for i in split:
        if len(i) > 8:
            l += 1
    return l / len(split)
 
example = ""
 
with open("formalSentences.txt",encoding="utf8") as f:
    for line in f:
        example = example + line
 
print(str(int(shortLong(example) * 100)) + "%")
print("Elapsed time: {:.5f}s".format(sum(timeit.repeat("shortLong(example)",globals=globals(),number=1,repeat=10))/10))
```
shortLong() returns 13%.

The issue is that running shortLong with our (admittedly huge) string takes us a 20th of a second. Not a problem when we run the script once, or even when running it tens of times. However, we plan to use this as just one step of many in our analysis, and we plan to run this analysis on thousands of Wikipedia articles. Now we have a problem.

We have a few options to optimize our code. For one, we’re wasting a lot of time by creating a for loop and iterating on our l variable. If we have sufficient knowledge of Python, we could very likely reduce this time greatly. However, even well-optimized Python is far from fast.

## Solved With Rust

We’ve established rust is fast. So, even though we won’t be able to code it in 10 seconds like with Python, let’s implement shortLong in Rust.

First, in your terminal or command prompt, we run cargo new short_long. Then, in the short_long directory, we navigate to ./src. Here, we create our lib.rs file, and put our method in it.

```rust
pub fn short_long(the_string: &str)->f64{
    let split:Vec<&str> = the_string.split(char::is_whitespace).filter(|&s| s != "the" && s != "a").collect();
.collect();
    let mut l = 0.0;
    for i in &split{
        if i.len() > 8{
            l = l + 1.0;
        }
    }
    println!("Length: {}",split.len());
    return l / (split.len() as f64);
}
```


That was pretty simple. We can add a main method and run it a few times shows that it’s pretty fast compared to Python, and nets us the same percentage<sup>1</sup> as in Python. But now what?

## The Foreign-Function-Interface

The Foreign Function Interface, or FFI, is a way that a developer writing code in one language can use functions built in another.

Through the extern keyword, Rust offers ways to interact with other languages using C-like bindings and data. Meanwhile, a number of libraries for Python offer ways to call these functions.

The library we’ll be using is CFFI.

## Exposing Our Rust Function
When you compile Rust code, the Rust compiler makes a number of changes and optimizations. One of these is name mangling, which changes the name of functions. This is ideal when only other Rust code that knows about this mangling calls our code, but not ideal when we’re calling the function from Python (and need to know the name of the function).

Luckily, a number of Rust compiler directives exist. We will add the “no mangle” directive to our function, so the compiler knows to leave the name alone. In addition, so that the compiler knows we want to expose this function for external use, we will also add the extern keyword to our function.

```rust
#[no_mangle]
pub extern "C" fn short_long(the_string: &str)->f64{
    let split:Vec<&str> = the_string.split(char::is_whitespace).filter(|&s| s != "the").collect();
    let mut l = 0.0;
    for i in &split{
        if i.len() > 8{
            l = l + 1.0;
        }
    }
    return l / (split.len() as f64);
}
```

However, now we get a warning that &str is not FFI safe. This is because Rust’s FFI is built to interact with C code, and there is no string slice in C.

### Slices & Pointers in Rust

Rust slices consist of two parts: a pointer (to the beginning of the data), and a length (so we know not to index outside of our data).
This means, even though it violates Rust’s memory safety principle, we can create our own slice from a pointer and a length. C can handle both of these things, so if we rewrite our function to accept these parameters, we can expose it without worrying about string slices not existing in C.

```rs
use std::slice;
use std::str;
#[no_mangle]
pub extern "C" fn short_long(ptr: * const u8, len: usize)->f64{
    unsafe{
        let the_slice:&[u8] = slice::from_raw_parts(ptr,len);
        let the_string = str::from_utf8_unchecked(the_slice);
        let split:Vec<&str> = the_string.split(char::is_whitespace).filter(|&s| s != "the").collect();
        let mut l = 0.0;
        for i in &split{
            if i.len() > 8{
                l = l + 1.0;
            }
        }
        return l / (split.len() as f64);
    }
}
```

There are three changes here - first, we change the &str parameter to a pointer of type u8 (AKA a byte) and a length. Next, we wrap our function logic in unsafe{} (since what we’re doing can break very easily if the wrong parameters are provided, and Rust hates that). Finally, we create the_string from our pointer by creating the u8 slice, then creating a &str from this slice.

One important fact to note is that we’re using a pointer with type u8. Since we’re sending our string as C-like data, we can’t just send Rust chars, nor Python characters. We have to send C characters (which are, under the hood, just 8-bit numbers) and convert these to a Rust string. In fact, we aren’t even just sending C characters. We are sending the location in memory where our Rust function can find some C characters.

This is a much more involved process, but it’s a sacrifice we make to have our method play nicely with CFFI.

Finally, we will modify cargo.toml to direct cargo to build a shared object or linked library file from our code.

```toml
[package]
name = "short_long"
version = "0.1.0"

[lib]
crate-type = ["dylib"]
```

Now, when we run cargo build --release from the same directory as cargo.toml and src, we will have our final product in shortlong/target/release.

On Windows, this file is a .dll (or Dynamic-Link library), on Linux distros, this file is a .so (shared object), and on macOS, we will have a .dylib file (Dynamic Library).

## Calling our Rust function

First, ensure you have cffi installed.
```
pip install cffi
```
Now, let’s copy our python script and add some code to the beginning.

```python
from cffi import FFI
ffi = FFI()
lib = ffi.dlopen("short_long/target/release/short_long.dll")
ffi.cdef("""
    double short_long(const char *, uint64_t);
"""
)
```

The two important things to investigate here is ffi.dlopen() and ffi.cdef().
ffi.dlopen() is pretty simple - we’re just telling our foreign-function interface what library to load. Note the argument you put in here will depend on where your Python script is, and what file extension your library has.

More interesting is ffi.cdef().
We’re defining our function for our ffi using C syntax. This can take a few extra steps, since Rust has different names for datatypes than C.
In Rust, our function returned an f64. However, f64 is not the name of a type in C. The C type for a 64-bit float is a double. Next, we name our function how we named it in Rust. 
We tell our FFI that short_long gets a char (remember: C char, not Python or Rust char) pointer (which corresponds with our u8 pointer in Rust) and an unsigned 64-bit integer to represent the length of the array. On 64-bit architectures, usize is a 64-bit integer, while on 32-bit architectures it is a 32-bit integer.

Now that we have defined how our method is called, we can call it in Python.

```python
string = example.encode()
cstr = ffi.new("char[]", string)
print(lib.short_long(cstr,len(cstr)))
```

Note that we don’t just give a string to our short_long method.

First, we encode our string. In Python, String.encode() defaults to utf8 encoding, which is exactly the type we want, since we’re working with C chars.

```python
string = example.encode()
```

Next, we create a C char array in memory and assign cstr to be a pointer towards the beginning of it.
```python
cstr = ffi.new("char[]", string)
```
Finally, we can call our method from lib by providing it our pointer and the length of our array.
```python
print(lib.short_long(cstr,len(cstr)))
```
And it works!

## Comparison
Let’s time our original program against our new one that makes use of our Rust code.

We’ll use the python timeit library.

First, we’ll time our original Python implementation.
```py
import timeit
def shortLong(string):
    split = string.split()
    split = [i for i in split if (i != "the") & (i != "a")]
    l = 0
    for i in split:
        if len(i) > 8:
            l += 1
    return l / len(split)


#LOAD STRING
example = ""
with open("formalSentences.txt",encoding="utf8") as f:
    for line in f:
        example = example + line

#PRINT RESULT
print("Pure Python: ")
print(str(int(shortLong(example) * 100)) + "%")

#TIMEIT
print("Elapsed time: {:.5f}s".format(sum(timeit.repeat("shortLong(example)",globals=globals(),number=1,repeat=20))/20))
```
So, taking the average runtime of 20 runs of our Python implementation, we have 0.05467 seconds, or about a 20th of a second.
```
Pure Python:
13%
Elapsed time: 0.05467s
```

Now, let’s run our Rust implementation.
```rs
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
        example = example + line

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
```
The same operation in Rust gives us a run time of 0.01009 seconds, or one one-hundredth of a second. 
```
With Rust:
13%
Elapsed time: 0.01009s
```

So, even in this already pretty fast example, running a Rust function using the CFFI takes 1/5th the time of executing in Python.

Consider what is possible in tasks that take Python many seconds or even minutes to complete.

Using languages other than Python to speed up your Python code is very useful, and in many cases, practically necessary. Many popular Python libraries such as NumPy and scikit are largely bindings for code written in much faster languages. When trying to figure out how to optimize your Python code, you may find that libraries written in other languages appear often in suggestions on StackOverflow. If you can, you should use built-ins provided by these libraries to speed up your code - afterall, your time is valuable.

While exploring data science or other areas of interest using Python, you may find that even after making as many optimizations using NumPy or clever Python as you could, you are still faced with a task that takes hours. In this case, augmenting your Python code with a language such as Rust is your only choice.


The final code resulting from this project is available at [here](https://github.com/RayElg/RustPythonCFFI)

## Notes & References

1: Note that after rounding to the nearest percentage, our value is the same. However, the full number is slightly different. This is due to split in Rust behaving differently than split in Python, and a different number of words being returned. When moving an implementation to a different language, you need to make sure any differences are tolerable for your use case.
Using Arrays, Structs, etc. with CFFI: [https://cffi.readthedocs.io/en/latest/using.html]
Python encoding: https://docs.python.org/3/library/codecs.html#codec-base-classes
The Rust extern keyword: https://doc.rust-lang.org/std/keyword.extern.html
cdef in CFFI: https://cffi.readthedocs.io/en/latest/cdef.html#ffi-ffibuilder-cdef-declaring-types-and-functions
