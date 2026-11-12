use std::process::Command;

#[test]
fn cli_reports_compiled_version_and_rejects_overflow() {
    let binary = env!("CARGO_BIN_EXE_foundation-demo");
    let version = Command::new(binary).arg("--version").output().unwrap();
    assert!(version.status.success());
    assert_eq!(
        String::from_utf8(version.stdout).unwrap().trim(),
        env!("CARGO_PKG_VERSION")
    );
    let overflow = Command::new(binary)
        .arg(i64::MAX.to_string())
        .output()
        .unwrap();
    assert_eq!(overflow.status.code(), Some(2));
}
