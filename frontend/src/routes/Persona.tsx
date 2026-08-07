import { useParams } from "react-router-dom";

export default function Persona() {
  const { id } = useParams();
  return <p>Persona {id} — tarea 13.</p>;
}
