use std::slice;
use std::str;
#[no_mangle]
pub extern "C" fn short_long(ptr: * const u8, len: usize)->f64{
    unsafe{
        let the_slice:&[u8] = slice::from_raw_parts(ptr,len);
        let the_string = str::from_utf8_unchecked(the_slice);
        let split:Vec<&str> = the_string.split(char::is_whitespace).filter(|&s| s != "the" && s != "a").collect();
        let mut l = 0.0;
        for i in &split{
            if i.len() > 8{
                l = l + 1.0;
            }
        }
        return l / (split.len() as f64);
    }
}
