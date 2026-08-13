import type { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  children: ReactNode;
};

export function SectionCard({ title, children }: SectionCardProps) {
  return (
    <section
      style={{
        padding: "24px",
        borderRadius: "20px",
        border: "1px solid #d4ccb9",
        background: "#fffdf8",
      }}
    >
      <h2 style={{ marginTop: 0 }}>{title}</h2>
      <div>{children}</div>
    </section>
  );
}

