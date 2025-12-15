import React, { useEffect, useState } from "react";
import "./App.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

type Scene = {
  scene_number: number;
  prompt: string;
  image_url: string | null;
  image_path?: string | null;
  negative_prompt?: string | null;
};

type StoryResponse = {
  story_id: string;
  status: string;
  story_title: string;
  character_concept?: string | null;
  visual_style: string;
  character_name?: string | null;
  scenes: Scene[];
  created_at: string;
  output_dir?: string | null;
};

function App() {
  const [prompt, setPrompt] = useState("");
  const [maxScenes, setMaxScenes] = useState(5);
  const [removeWatermarks, setRemoveWatermarks] = useState(false);

  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [storyId, setStoryId] = useState<string | null>(null);
  const [story, setStory] = useState<StoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!storyId || !polling) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(
          `${API_BASE_URL}/api/v1/story/story/${storyId}`
        );
        if (!res.ok) {
          throw new Error("Erreur lors de la récupération de la story");
        }
        const data: StoryResponse = await res.json();
        setStory(data);

        if (data.status.toLowerCase() === "completed") {
          setPolling(false);
        }
      } catch (err: any) {
        console.error(err);
        setError(err.message || "Erreur inconnue");
        setPolling(false);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [storyId, polling]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setStory(null);
    setStoryId(null);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/story/generate-story`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt,
          max_num_scenes: maxScenes,
          remove_watermarks: removeWatermarks,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Erreur lors de la génération de la story");
      }

      const data: StoryResponse = await res.json();
      setStory(data);
      setStoryId(data.story_id);
      setPolling(true);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #0f172a, #020617)",
        color: "#e5e7eb",
        display: "flex",
        justifyContent: "center",
        padding: "2rem",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "960px",
          backgroundColor: "rgba(15, 23, 42, 0.9)",
          borderRadius: "1.5rem",
          padding: "2rem",
          boxShadow: "0 25px 50px -12px rgba(15, 23, 42, 0.9)",
          border: "1px solid rgba(148, 163, 184, 0.3)",
        }}
      >
        <h1 style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>
          Générateur de séquences d&apos;images
        </h1>
        <p style={{ color: "#9ca3af", marginBottom: "1.5rem" }}>
          Entrez un prompt d&apos;histoire, cliquez sur générer, puis attendez
          que les images soient créées par le backend.
        </p>

        <form onSubmit={handleSubmit} style={{ marginBottom: "2rem" }}>
          <div style={{ marginBottom: "1rem" }}>
            <label
              htmlFor="prompt"
              style={{
                display: "block",
                marginBottom: "0.5rem",
                fontWeight: 500,
              }}
            >
              Prompt
            </label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Décris ta scène ou ton histoire..."
              required
              rows={4}
              style={{
                width: "100%",
                borderRadius: "0.75rem",
                padding: "0.75rem 1rem",
                border: "1px solid rgba(148,163,184,0.5)",
                backgroundColor: "rgba(15,23,42,0.9)",
                color: "#e5e7eb",
                resize: "vertical",
              }}
            />
          </div>

          <div
            style={{
              display: "flex",
              gap: "1rem",
              flexWrap: "wrap",
              marginBottom: "1rem",
            }}
          >
            <div style={{ minWidth: "160px" }}>
              <label
                htmlFor="maxScenes"
                style={{
                  display: "block",
                  marginBottom: "0.5rem",
                  fontWeight: 500,
                }}
              >
                Nombre de scènes
              </label>
              <input
                id="maxScenes"
                type="number"
                min={1}
                max={10}
                value={maxScenes}
                onChange={(e) => setMaxScenes(Number(e.target.value) || 1)}
                style={{
                  width: "100%",
                  borderRadius: "0.75rem",
                  padding: "0.5rem 0.75rem",
                  border: "1px solid rgba(148,163,184,0.5)",
                  backgroundColor: "rgba(15,23,42,0.9)",
                  color: "#e5e7eb",
                }}
              />
            </div>

            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                cursor: "pointer",
                marginTop: "1.75rem",
              }}
            >
              <input
                type="checkbox"
                checked={removeWatermarks}
                onChange={(e) => setRemoveWatermarks(e.target.checked)}
              />
              <span>Supprimer les watermarks</span>
            </label>
          </div>

          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            style={{
              marginTop: "0.5rem",
              borderRadius: "9999px",
              padding: "0.75rem 1.5rem",
              border: "none",
              cursor: loading ? "wait" : "pointer",
              background: "linear-gradient(135deg, #22c55e, #16a34a)",
              color: "#0b1120",
              fontWeight: 600,
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? "Génération en cours..." : "Générer la séquence"}
          </button>

          {polling && !loading && (
            <span style={{ marginLeft: "1rem", color: "#a5b4fc" }}>
              Génération d&apos;images en arrière-plan…
            </span>
          )}
        </form>

        {error && (
          <div
            style={{
              marginBottom: "1.5rem",
              padding: "0.75rem 1rem",
              borderRadius: "0.75rem",
              backgroundColor: "rgba(239,68,68,0.1)",
              color: "#fecaca",
              border: "1px solid rgba(248,113,113,0.4)",
            }}
          >
            {error}
          </div>
        )}

        {story && (
          <div>
            <div style={{ marginBottom: "1rem" }}>
              <h2 style={{ fontSize: "1.25rem", marginBottom: "0.25rem" }}>
                {story.story_title}
              </h2>
              <p style={{ color: "#9ca3af", marginBottom: "0.25rem" }}>
                ID: {story.story_id}
              </p>
              <p style={{ color: "#a5b4fc", marginBottom: "0.5rem" }}>
                Statut: {story.status}
              </p>
              {story.character_name && (
                <p style={{ color: "#9ca3af" }}>
                  Personnage: {story.character_name} — Style:{" "}
                  {story.visual_style}
                </p>
              )}
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                gap: "1rem",
              }}
            >
              {story.scenes.map((scene) => (
                <div
                  key={scene.scene_number}
                  style={{
                    backgroundColor: "rgba(15,23,42,0.9)",
                    borderRadius: "0.75rem",
                    padding: "0.75rem",
                    border: "1px solid rgba(148,163,184,0.3)",
                  }}
                >
                  <h3
                    style={{
                      fontWeight: 600,
                      marginBottom: "0.25rem",
                    }}
                  >
                    Scène {scene.scene_number}
                  </h3>
                  <p
                    style={{
                      fontSize: "0.9rem",
                      color: "#d1d5db",
                      marginBottom: "0.5rem",
                    }}
                  >
                    {scene.prompt}
                  </p>
                  {scene.image_url ? (
                    <img
                      src={`${API_BASE_URL}${scene.image_url}`}
                      alt={`Scène ${scene.scene_number}`}
                      style={{
                        width: "100%",
                        borderRadius: "0.5rem",
                        objectFit: "cover",
                        maxHeight: "260px",
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        borderRadius: "0.5rem",
                        border: "1px dashed rgba(148,163,184,0.4)",
                        padding: "1.5rem 1rem",
                        textAlign: "center",
                        color: "#9ca3af",
                        fontSize: "0.9rem",
                      }}
                    >
                      Image en cours de génération…
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
