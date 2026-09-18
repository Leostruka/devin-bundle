use pyo3::prelude::*;

/// Sum a list of f64 in one pass.
#[pyfunction]
fn fast_sum(values: Vec<f64>) -> f64 {
    values.iter().sum()
}

/// Sieve of Eratosthenes — all primes < n.
/// Releases the GIL while sieving: the golden pattern for CPU-bound work.
#[pyfunction]
fn primes_below(py: Python<'_>, n: u64) -> Vec<u64> {
    py.detach(|| {
        let n = n as usize;
        if n < 2 {
            return Vec::new();
        }
        let mut sieve = vec![true; n];
        sieve[0] = false;
        sieve[1] = false;
        let mut i = 2;
        while i * i < n {
            if sieve[i] {
                for j in (i * i..n).step_by(i) {
                    sieve[j] = false;
                }
            }
            i += 1;
        }
        (2..n as u64).filter(|&p| sieve[p as usize]).collect()
    })
}

/// `import fast_math`
#[pymodule]
fn fast_math(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fast_sum, m)?)?;
    m.add_function(wrap_pyfunction!(primes_below, m)?)?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
