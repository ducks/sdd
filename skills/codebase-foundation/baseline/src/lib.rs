//! Checked arithmetic used by the command-line application.
pub fn double(value: i64) -> Option<i64> {
    value.checked_mul(2)
}

#[cfg(test)]
mod tests {
    use super::double;
    #[test]
    fn doubles_signed_input() {
        assert_eq!(double(-7), Some(-14));
        assert_eq!(double(0), Some(0));
    }
    #[test]
    fn rejects_overflow() {
        assert_eq!(double(i64::MAX), None);
    }
}
