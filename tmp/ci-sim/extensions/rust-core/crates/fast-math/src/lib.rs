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
    py.detach(|| sieve_below(n))
}

fn sieve_below(n: u64) -> Vec<u64> {
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
}

/// `import fast_math`
#[pymodule]
fn fast_math(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fast_sum, m)?)?;
    m.add_function(wrap_pyfunction!(primes_below, m)?)?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fast_sum_empty_and_values() {
        assert_eq!(fast_sum(vec![]), 0.0);
        assert_eq!(fast_sum(vec![1.5, -2.25, 3.75]), 3.0);
    }

    #[test]
    fn sieve_below_two_is_empty() {
        assert!(sieve_below(0).is_empty());
        assert!(sieve_below(1).is_empty());
        assert!(sieve_below(2).is_empty());
    }

    #[test]
    fn sieve_below_30_lists_primes() {
        assert_eq!(sieve_below(30), vec![2, 3, 5, 7, 11, 13, 17, 19, 23, 29]);
    }

    #[test]
    fn sieve_100k_prime_count() {
        assert_eq!(sieve_below(100_000).len(), 9_592);
    }
}
