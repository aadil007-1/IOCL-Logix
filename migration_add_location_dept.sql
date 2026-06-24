-- Migration: Add missing 'location_dept' and 'role' columns to work_logs
-- Run this in your Supabase SQL Editor if these columns are missing

-- Add location_dept column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'work_logs'
          AND column_name = 'location_dept'
    ) THEN
        ALTER TABLE public.work_logs ADD COLUMN location_dept text;
        RAISE NOTICE 'Column location_dept added successfully.';
    ELSE
        RAISE NOTICE 'Column location_dept already exists, skipping.';
    END IF;
END
$$;

-- Add role column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'work_logs'
          AND column_name = 'role'
    ) THEN
        ALTER TABLE public.work_logs ADD COLUMN role text;
        RAISE NOTICE 'Column role added successfully.';
    ELSE
        RAISE NOTICE 'Column role already exists, skipping.';
    END IF;
END
$$;
