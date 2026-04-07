-- KAN-70: Add DINOv2 reference embedding column to alerts table.
-- Used by the instance_matcher for "same item" (exact) matching.
-- Separate from reference_embedding (FashionSigLIP) which is used for style similarity.

ALTER TABLE alerts
    ADD COLUMN IF NOT EXISTS reference_dinov2_embedding JSONB DEFAULT NULL;
