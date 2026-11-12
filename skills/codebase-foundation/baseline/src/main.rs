fn main() {
    let input = std::env::args().nth(1);
    if input.as_deref() == Some("--version") {
        println!("{}", env!("CARGO_PKG_VERSION"));
        return;
    }
    match input
        .and_then(|s| s.parse::<i64>().ok())
        .and_then(foundation_demo::double)
    {
        Some(value) => println!("{value}"),
        None => {
            eprintln!("usage: foundation-demo INTEGER (must not overflow)");
            std::process::exit(2);
        }
    }
}
