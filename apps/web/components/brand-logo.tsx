import Image from "next/image";
import logo from "../public/peyajflow-logo.png";

export function BrandLogo() {
  return (
    <Image
      src={logo}
      alt="PeyajFlow"
      className="brand-logo"
      width={162}
      height={31}
      unoptimized
    />
  );
}
