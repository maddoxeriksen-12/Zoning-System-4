--
-- PostgreSQL database dump
--

\restrict IgF7rkWfjm8DQ960iRuB8eFnOv1UhN0LlwztFcURraN3gITS0pwm1KtNsQhrWns

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: zoning_user
--

INSERT INTO public.documents VALUES ('0e7ab96d-06f3-46b1-8e39-4a443f0e5d18', '4b6e32ad974b4d8c8622e7e320b3c2fe_test_zoning_document.txt', 'test_zoning_document.txt', '/app/uploads/4b6e32ad974b4d8c8622e7e320b3c2fe_test_zoning_document.txt', 113, 'text/plain', 'Monmouth County', 'NJ', '2025-09-25 18:44:54.120708+00', 'uploaded', NULL, NULL, NULL, NULL, '2025-09-25 18:44:54.120708+00', '2025-09-25 18:44:54.120708+00');
INSERT INTO public.documents VALUES ('9d22f209-bbca-4661-bc5f-ae30bd929dec', 'a6a176c0848a4432b072ca8c624bd3bd_test_zoning_document.txt', 'test_zoning_document.txt', '/app/uploads/a6a176c0848a4432b072ca8c624bd3bd_test_zoning_document.txt', 113, 'text/plain', 'Monmouth County', 'NJ', '2025-09-25 18:45:27.473407+00', 'uploaded', NULL, NULL, NULL, NULL, '2025-09-25 18:45:27.473407+00', '2025-09-25 18:45:27.473407+00');
INSERT INTO public.documents VALUES ('e9004dab-08e0-4032-bf85-86057974ac93', '185fb338848e4689876599f016c05dfb_test_zoning_document.txt', 'test_zoning_document.txt', '/app/uploads/185fb338848e4689876599f016c05dfb_test_zoning_document.txt', 113, 'text/plain', 'Monmouth County', 'NJ', '2025-09-25 18:45:49.791624+00', 'failed', '2025-09-25 18:45:49.862096+00', '2025-09-25 18:45:49.91902+00', NULL, 'Grok API error: 400 - {"code":"Client specified an invalid argument","error":"Incorrect API key provided: YO***RE. You can obtain an API key from https://console.x.ai."}', '2025-09-25 18:45:49.791624+00', '2025-09-25 18:45:49.91902+00');
INSERT INTO public.documents VALUES ('9f8e7644-03cf-4b22-bb85-2d77aa9e6e24', '4602f53bfe1a4539b991af4c799714d7_test_zoning_with_grok.txt', 'test_zoning_with_grok.txt', '/app/uploads/4602f53bfe1a4539b991af4c799714d7_test_zoning_with_grok.txt', 188, 'text/plain', 'Test City', 'NJ', '2025-09-25 18:53:05.52946+00', 'failed', '2025-09-25 18:53:05.556402+00', '2025-09-25 18:53:05.566592+00', NULL, 'Grok API error: 400 - {"code":"Client specified an invalid argument","error":"Incorrect API key provided: YO***RE. You can obtain an API key from https://console.x.ai."}', '2025-09-25 18:53:05.52946+00', '2025-09-25 18:53:05.566592+00');
INSERT INTO public.documents VALUES ('21a186d6-c431-4050-9566-7afbb98d3e72', 'ea745b64e2fe4a2bbf08391dcc9c72f9_test_zoning_with_grok.txt', 'test_zoning_with_grok.txt', '/app/uploads/ea745b64e2fe4a2bbf08391dcc9c72f9_test_zoning_with_grok.txt', 188, 'text/plain', 'Test City', 'NJ', '2025-09-25 18:55:32.470536+00', 'failed', '2025-09-25 18:55:32.497433+00', '2025-09-25 18:55:32.552392+00', NULL, 'Grok API error: 404 - {"code":"Some requested entity was not found","error":"The model grok-beta was deprecated on 2025-09-15 and is no longer accessible via the API. Please use grok-3 instead."}', '2025-09-25 18:55:32.470536+00', '2025-09-25 18:55:32.552392+00');
INSERT INTO public.documents VALUES ('65f46be7-a58f-41e1-a091-6ceaed784fe8', '05329e400b344196b463d8eb3e56953f_test_zoning_with_grok.txt', 'test_zoning_with_grok.txt', '/app/uploads/05329e400b344196b463d8eb3e56953f_test_zoning_with_grok.txt', 188, 'text/plain', 'Test City', 'NJ', '2025-09-25 18:56:12.921322+00', 'failed', '2025-09-25 18:56:12.93988+00', '2025-09-25 18:56:12.947495+00', NULL, 'Grok API error: 404 - {"code":"Some requested entity was not found","error":"The model grok-beta was deprecated on 2025-09-15 and is no longer accessible via the API. Please use grok-3 instead."}', '2025-09-25 18:56:12.921322+00', '2025-09-25 18:56:12.947495+00');
INSERT INTO public.documents VALUES ('e1ecca60-f0f3-455b-bda4-94cf98eb6821', '7fa1e024a8ac442a96bedf0fc5dbc334_test_zoning_with_grok.txt', 'test_zoning_with_grok.txt', '/app/uploads/7fa1e024a8ac442a96bedf0fc5dbc334_test_zoning_with_grok.txt', 188, 'text/plain', 'Test City', 'NJ', '2025-09-25 18:56:56.168072+00', 'completed', '2025-09-25 18:56:56.195881+00', '2025-09-25 18:56:56.206604+00', '{
  "zoning_districts": {
    "Residential Districts": {
      "primary_use": "Residential housing and related uses"
    }
  },
  "key_regulations": {
    "Setback Requirements": "Specific front, side, and rear setbacks are mandated for all structures within residential districts (exact measurements not provided in the excerpt).",
    "Building Height Limits": "Height restrictions are imposed on buildings within residential zones (specific limits not detailed in the provided text)."
  },
  "permitted_uses": {
    "Residential Districts": [
      "Single-family homes",
      "Related accessory uses (specific uses not detailed in the excerpt)"
    ]
  },
  "special_provisions": {
    "Overlays or Exceptions": "No specific overlays, exceptions, or special provisions mentioned in the provided text excerpt."
  },
  "summary": "This zoning ordinance document for Test City, NJ, outlines regulations primarily for residential zoning districts. It includes provisions for setbacks and building height limits, though specific details are not provided in the excerpt. The primary focus is on residential uses, with permitted uses centered around housing. No special provisions or overlays are mentioned in the limited text provided."
}', NULL, '2025-09-25 18:56:56.168072+00', '2025-09-25 18:56:56.206604+00');
INSERT INTO public.documents VALUES ('dbc80575-023c-4b01-bb01-d4415bde192e', 'c237d8306df24d29881da23de88a28c7_test_grok4.txt', 'test_grok4.txt', '/app/uploads/c237d8306df24d29881da23de88a28c7_test_grok4.txt', 201, 'text/plain', 'Sample City', 'NJ', '2025-09-25 19:01:52.356561+00', 'completed', '2025-09-25 19:01:52.390371+00', '2025-09-25 19:01:52.401978+00', '{
  "zoning_districts": [
    {
      "name": "Commercial Zoning Districts",
      "primary_uses": "Not specified in detail; generally intended for commercial activities based on document description."
    }
  ],
  "key_regulations": [
    "Parking requirements: Specific standards for parking in commercial districts (details not elaborated).",
    "Building density regulations: Controls on density for developments (details not elaborated).",
    "Setbacks, height limits: Not mentioned in the provided text.",
    "Other: The document is a test version, limiting full regulatory details."
  ],
  "permitted_uses": {
    "Commercial Zoning Districts": "Commercial uses implied, but no specific permitted uses listed in the text."
  },
  "special_provisions": [
    "No special zoning provisions, overlays, or exceptions explicitly mentioned.",
    "Document noted as a test ordinance for model evaluation, with text length limited for API purposes."
  ],
  "summary": "This test zoning ordinance for Sample City, NJ, is a placeholder document focused on commercial zoning districts, parking requirements, and building density regulations. It lacks detailed content, serving primarily as a testing artifact for the Grok-4-fast-reasoning model, with no comprehensive regulatory specifics provided."
}', NULL, '2025-09-25 19:01:52.356561+00', '2025-09-25 19:01:52.401978+00');
INSERT INTO public.documents VALUES ('f97c6d5a-edc2-418d-919c-ce9c2878de77', '77f6f706b3b145f686530698b78ea247_test_verify.txt', 'test_verify.txt', '/app/uploads/77f6f706b3b145f686530698b78ea247_test_verify.txt', 40, 'text/plain', 'Test City', 'NJ', '2025-09-25 19:48:32.044139+00', 'completed', '2025-09-25 19:48:32.071544+00', '2025-09-25 19:48:32.077269+00', '{
  "zoning_districts": "No zoning districts are mentioned in the provided document text.",
  "key_regulations": "No key regulations, setbacks, height limits, or density requirements are mentioned in the provided document text.",
  "permitted_uses": "No permitted uses by district are mentioned in the provided document text.",
  "special_provisions": "No special zoning provisions, overlays, or exceptions are mentioned in the provided document text.",
  "summary": "The provided document text appears to be a placeholder for testing purposes (''Test document for function verification # Limit text length for API'') and contains no substantive information about zoning ordinances for Test City, NJ. No extractable zoning details are available."
}', NULL, '2025-09-25 19:48:32.044139+00', '2025-09-25 19:48:32.077269+00');
INSERT INTO public.documents VALUES ('9c18d25f-4ceb-4fbf-990c-40b96c460e4f', '266d2a1eb5e2459eb977ad99e47cfb46_test_zoning.txt', 'test_zoning.txt', '/app/uploads/266d2a1eb5e2459eb977ad99e47cfb46_test_zoning.txt', 254, 'text/plain', 'TestTown', 'NJ', '2025-09-25 20:39:57.312878+00', 'failed', '2025-09-25 20:39:57.344997+00', '2025-09-25 20:39:57.378845+00', NULL, 'Grok API error: 400 - {"code":"Client specified an invalid argument","error":"Incorrect API key provided: YO***RE. You can obtain an API key from https://console.x.ai."}', '2025-09-25 20:39:57.312878+00', '2025-09-25 20:39:57.378845+00');


--
-- PostgreSQL database dump complete
--

\unrestrict IgF7rkWfjm8DQ960iRuB8eFnOv1UhN0LlwztFcURraN3gITS0pwm1KtNsQhrWns

