import { useState } from "react";

// ── DATA ─────────────────────────────────────────────────────
// RESULTS (singles) and FADE_RESULTS below are AUTO-GENERATED from the
// graded posted_cards by generate_record_data.py --inject. Full history
// (from 2026-05-08) lives in the posted cards. Do NOT hand-edit between
// the markers; it gets overwritten every run.
// RL_RESULTS (below) stays hand-maintained — run lines can't be auto-graded.
// >>> AUTO-GENERATED DATA BEGIN — do not edit between markers
// Generated: 2026-09-26T10:14:51  (source: posted_cards/)
const RESULTS = [
  {
    date: "2026-09-23",
    sport: "MLB",
    plays: [
      {player:"Kevin Gausman", prop:"K OVER 5.5", odds:-151, tier:"AUTO", hit:true, actual:7, note:"7 Ks — WIN", hit_prob:0.895},
      {player:"Logan Henderson", prop:"K OVER 5.5", odds:-113, tier:"T1", hit:false, actual:3, note:"3 Ks — LOSS", hit_prob:0.758},
      {player:"Nolan Arenado", prop:"H OVER 1.5", odds:175, tier:"T1", hit:false, actual:1, note:"1 hits — LOSS", hit_prob:0.654},
      {player:"Alejandro Kirk", prop:"H OVER 0.5", odds:-227, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.882},
      {player:"Bo Bichette", prop:"H OVER 0.5", odds:-249, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.906},
      {player:"Brooks Lee", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.882},
      {player:"Carson Benge", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.866},
      {player:"Cole Carrigg", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.889},
      {player:"Dominic Canzone", prop:"H OVER 0.5", odds:-207, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.929},
      {player:"Fernando Tatis Jr.", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.885},
      {player:"Jake Cronenworth", prop:"H OVER 0.5", odds:-105, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.675},
      {player:"Jo Adell", prop:"H OVER 0.5", odds:-185, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.94},
      {player:"Jose Altuve", prop:"H OVER 0.5", odds:-212, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.839},
      {player:"Jose Ramirez", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.825},
      {player:"Mauricio Dubon", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.95},
      {player:"Teoscar Hernandez", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.835},
      {player:"Trevor Story", prop:"H OVER 0.5", odds:-185, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.95},
      {player:"Yordan Alvarez", prop:"H OVER 0.5", odds:-241, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.879},
      {player:"Zack Gelof", prop:"H OVER 0.5", odds:-185, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.82},
    ],
    parlays: [],
  },
  {
    date: "2026-09-20",
    sport: "MLB",
    plays: [
      {player:"Hunter Brown", prop:"K OVER 6.5", odds:105, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.683},
      {player:"Jacob deGrom", prop:"K OVER 5.5", odds:105, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.696},
      {player:"Patrick Sandoval", prop:"K OVER 4.5", odds:125, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.679},
      {player:"Will Warren", prop:"K OVER 4.5", odds:-105, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.721},
      {player:"Alejandro Kirk", prop:"H OVER 0.5", odds:-193, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.891},
      {player:"Brandon Lowe", prop:"H OVER 0.5", odds:-182, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.913},
      {player:"Brett Baty", prop:"H OVER 0.5", odds:110, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.691},
      {player:"Chandler Simpson", prop:"TB OVER 1.5", odds:153, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.569},
      {player:"Connor Norby", prop:"H OVER 0.5", odds:-231, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"Corey Seager", prop:"H OVER 0.5", odds:-220, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.906},
      {player:"Dustin Harris", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.907},
      {player:"Hao-Yu Lee", prop:"TB OVER 1.5", odds:141, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.483},
      {player:"Heriberto Hernandez", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.882},
      {player:"Jo Adell", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.916},
      {player:"Joey Ortiz", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.947},
      {player:"Jonathan Aranda", prop:"H OVER 0.5", odds:-196, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.894},
      {player:"Luke Keaschall", prop:"H OVER 0.5", odds:-246, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.832},
      {player:"Marcus Semien", prop:"H OVER 0.5", odds:-156, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.916},
      {player:"Mauricio Dubon", prop:"H OVER 0.5", odds:-201, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.937},
      {player:"Max Clark", prop:"H OVER 0.5", odds:-167, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"Nolan Arenado", prop:"H OVER 0.5", odds:-164, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.866},
      {player:"Riley Greene", prop:"H OVER 0.5", odds:-186, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.928},
      {player:"Ronny Simon", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.848},
      {player:"Trevor Story", prop:"H OVER 0.5", odds:-164, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.944},
      {player:"Ty France", prop:"TB OVER 1.5", odds:135, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.512},
    ],
    parlays: [],
  },
  {
    date: "2026-09-18",
    sport: "MLB",
    plays: [
      {player:"Cade Cavalli", prop:"K OVER 5.5", odds:-165, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.922},
      {player:"Josh Naylor", prop:"H OVER 1.5", odds:145, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.679},
      {player:"Ben Rice", prop:"H OVER 0.5", odds:-227, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.841},
      {player:"Brandon Lowe", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.848},
      {player:"Chandler Simpson", prop:"H OVER 0.5", odds:-242, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.854},
      {player:"Christian Koss", prop:"H OVER 0.5", odds:-115, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.675},
      {player:"Cooper Pratt", prop:"H OVER 0.5", odds:-203, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.832},
      {player:"Corey Seager", prop:"H OVER 0.5", odds:-168, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.866},
      {player:"Dustin Harris", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.882},
      {player:"Gabriel Moreno", prop:"H OVER 0.5", odds:-241, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.891},
      {player:"George Springer", prop:"H OVER 0.5", odds:-243, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.841},
      {player:"Heriberto Hernandez", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.842},
      {player:"Jackson Merrill", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.907},
      {player:"Jake Bauers", prop:"H OVER 0.5", odds:-188, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.832},
      {player:"Jeremy Pena", prop:"TB OVER 1.5", odds:135, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.492},
      {player:"Jo Adell", prop:"H OVER 0.5", odds:-226, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.851},
      {player:"Joey Ortiz", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.922},
      {player:"Jonah Cox", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.925},
      {player:"Jonathan Aranda", prop:"H OVER 0.5", odds:-184, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.854},
      {player:"Kevin McGonigle", prop:"TB OVER 1.5", odds:120, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.508},
      {player:"Kyle Karros", prop:"H OVER 0.5", odds:-223, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.889},
      {player:"Marcus Semien", prop:"H OVER 0.5", odds:-196, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.876},
      {player:"Mauricio Dubon", prop:"H OVER 0.5", odds:-220, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.872},
      {player:"Max Clark", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.928},
      {player:"Riley Greene", prop:"H OVER 0.5", odds:-196, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.903},
      {player:"Sal Stewart", prop:"TB OVER 1.5", odds:135, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.529},
      {player:"Shea Langeliers", prop:"H OVER 0.5", odds:-189, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.941},
      {player:"TJ Rumfield", prop:"H OVER 0.5", odds:-244, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.914},
      {player:"Trevor Story", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.919},
    ],
    parlays: [],
  },
  {
    date: "2026-09-17",
    sport: "MLB",
    plays: [
      {player:"Brett Baty", prop:"H OVER 0.5", odds:-114, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.716},
      {player:"Carter Jensen", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.872},
      {player:"Elly De La Cruz", prop:"H OVER 0.5", odds:-223, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.909},
      {player:"Jake Bauers", prop:"H OVER 0.5", odds:-198, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.823},
      {player:"Jake Cronenworth", prop:"H OVER 0.5", odds:-234, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.889},
      {player:"Joey Ortiz", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.913},
      {player:"Josh Jung", prop:"TB OVER 1.5", odds:149, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.461},
      {player:"Juan Brito", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.859},
      {player:"Justin Crawford", prop:"H OVER 0.5", odds:-159, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.866},
      {player:"Marcus Semien", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.876},
      {player:"Max Clark", prop:"H OVER 0.5", odds:-184, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.903},
      {player:"Nick Gonzales", prop:"H OVER 0.5", odds:-233, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.848},
      {player:"Rafael Flores", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.938},
      {player:"Randal Grichuk", prop:"H OVER 0.5", odds:-209, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.928},
      {player:"Riley Greene", prop:"H OVER 0.5", odds:-199, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.863},
      {player:"Shea Langeliers", prop:"H OVER 0.5", odds:-180, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.944},
      {player:"TJ Rumfield", prop:"H OVER 0.5", odds:-256, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.794},
      {player:"Trevor Story", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.931},
      {player:"William Contreras", prop:"H OVER 0.5", odds:-234, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.848},
    ],
    parlays: [],
  },
  {
    date: "2026-09-09",
    sport: "MLB",
    plays: [
      {player:"Jake Bennett", prop:"K OVER 4.5", odds:-172, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.829},
      {player:"Kevin Gausman", prop:"K OVER 5.5", odds:-118, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.698},
      {player:"Yandy Diaz", prop:"H OVER 1.5", odds:179, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.653},
      {player:"A.J. Ewing", prop:"H OVER 0.5", odds:-202, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.82},
      {player:"Bryce Eldridge", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.867},
      {player:"Cal Raleigh", prop:"H OVER 0.5", odds:-181, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.904},
      {player:"Corey Seager", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.839},
      {player:"Dominic Canzone", prop:"H OVER 0.5", odds:-237, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.879},
      {player:"Gleyber Torres", prop:"H OVER 0.5", odds:-246, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.879},
      {player:"Ivan Herrera", prop:"H OVER 0.5", odds:-238, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.842},
      {player:"James McCann", prop:"H OVER 0.5", odds:-189, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.829},
      {player:"Javier Sanoja", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.91},
      {player:"Manny Machado", prop:"H OVER 0.5", odds:-207, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.842},
      {player:"Mike Trout", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.875},
      {player:"Pete Crow-Armstrong", prop:"H OVER 0.5", odds:-196, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.931},
      {player:"Salvador Perez", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.919},
      {player:"TJ Rumfield", prop:"H OVER 0.5", odds:-189, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"Teoscar Hernandez", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.925},
      {player:"Trea Turner", prop:"H OVER 0.5", odds:-228, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.878},
    ],
    parlays: [],
  },
  {
    date: "2026-09-08",
    sport: "MLB",
    plays: [
      {player:"Cal Raleigh", prop:"H OVER 0.5", odds:-180, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.879},
      {player:"Chandler Simpson", prop:"TB OVER 1.5", odds:140, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.483},
      {player:"Dominic Canzone", prop:"H OVER 0.5", odds:-198, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.879},
      {player:"Elly De La Cruz", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.885},
      {player:"Hector Rodriguez", prop:"H OVER 0.5", odds:-104, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.7},
      {player:"Ivan Herrera", prop:"H OVER 0.5", odds:-220, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.817},
      {player:"J.P. Crawford", prop:"H OVER 0.5", odds:-169, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.879},
      {player:"James Wood", prop:"H OVER 0.5", odds:-178, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.817},
      {player:"Mike Trout", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.875},
      {player:"Nathan Church", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.882},
      {player:"Pete Crow-Armstrong", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.891},
      {player:"Salvador Perez", prop:"H OVER 0.5", odds:-228, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.879},
      {player:"TJ Rumfield", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.95},
      {player:"Teoscar Hernandez", prop:"H OVER 0.5", odds:-216, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.925},
      {player:"Thomas Saggese", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.907},
    ],
    parlays: [],
  },
  {
    date: "2026-09-02",
    sport: "MLB",
    plays: [
      {player:"Jacob Lopez", prop:"K OVER 5.5", odds:-106, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.696},
      {player:"Trevor Rogers", prop:"K OVER 5.5", odds:-105, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.698},
      {player:"Alex Bregman", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.835},
      {player:"Bryce Harper", prop:"TB OVER 1.5", odds:114, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.561},
      {player:"Cody Bellinger", prop:"H OVER 0.5", odds:-214, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.857},
      {player:"Gleyber Torres", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.829},
      {player:"Junior Caminero", prop:"H OVER 0.5", odds:-238, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.944},
      {player:"Lawrence Butler", prop:"H OVER 0.5", odds:-193, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"Mookie Betts", prop:"H OVER 0.5", odds:-227, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.925},
      {player:"Nick Sogard", prop:"H OVER 0.5", odds:-196, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.85},
      {player:"Nico Hoerner", prop:"H OVER 0.5", odds:-192, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.835},
      {player:"Rafael Devers", prop:"H OVER 0.5", odds:-195, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.913},
      {player:"TJ Rumfield", prop:"H OVER 0.5", odds:-236, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"Tyler Stephenson", prop:"H OVER 0.5", odds:-180, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.884},
    ],
    parlays: [],
  },
  {
    date: "2026-08-28",
    sport: "MLB",
    plays: [
      {player:"Alec Burleson", prop:"H OVER 0.5", odds:-230, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.947},
      {player:"Andrew Vaughn", prop:"H OVER 0.5", odds:-202, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.95},
      {player:"Bryce Eldridge", prop:"H OVER 0.5", odds:-186, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.867},
      {player:"Bryce Harper", prop:"H OVER 0.5", odds:-220, tier:"AUTO", hit:false, actual:1, note:"1 hits — LOSS", hit_prob:0.857},
      {player:"Connor Norby", prop:"H OVER 0.5", odds:-151, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.95},
      {player:"Edmundo Sosa", prop:"H OVER 0.5", odds:-152, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.832},
      {player:"Elly De La Cruz", prop:"H OVER 0.5", odds:-192, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.86},
      {player:"Geraldo Perdomo", prop:"H OVER 0.5", odds:-179, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.817},
      {player:"Heriberto Hernandez", prop:"H OVER 0.5", odds:-214, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.857},
      {player:"J.T. Realmuto", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.832},
      {player:"Javier Baez", prop:"H OVER 0.5", odds:-119, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.684},
      {player:"Jonny Deluca", prop:"H OVER 0.5", odds:-177, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.854},
      {player:"Kaelen Culpepper", prop:"H OVER 0.5", odds:-158, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.879},
      {player:"Lawrence Butler", prop:"H OVER 0.5", odds:-193, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.87},
      {player:"Luis Lara", prop:"H OVER 0.5", odds:-212, tier:"AUTO", hit:"void", actual:0, note:"DNP / not in box scores — VOID", hit_prob:0.866},
      {player:"Luis Robert Jr.", prop:"H OVER 0.5", odds:-173, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.851},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-217, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.879},
      {player:"Ozzie Albies", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.888},
      {player:"Tristan Peters", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.804},
      {player:"Xavier Edwards", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.882},
      {player:"Zach Neto", prop:"H OVER 0.5", odds:-187, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.922},
    ],
    parlays: [],
  },
  {
    date: "2026-08-27",
    sport: "MLB",
    plays: [
      {player:"Alec Burleson", prop:"H OVER 0.5", odds:-212, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.947},
      {player:"Andrew Vaughn", prop:"H OVER 0.5", odds:-212, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.916},
      {player:"Brett Bateman", prop:"TB OVER 1.5", odds:155, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.471},
      {player:"Carson Benge", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.851},
      {player:"Cody Bellinger", prop:"H OVER 0.5", odds:-196, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.934},
      {player:"Connor Norby", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.947},
      {player:"Daulton Varsho", prop:"H OVER 0.5", odds:-159, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.869},
      {player:"Hunter Feduccia", prop:"H OVER 0.5", odds:125, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.718},
      {player:"Luis Lara", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.851},
      {player:"Mauricio Dubon", prop:"H OVER 0.5", odds:-193, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.878},
      {player:"William Contreras", prop:"TB OVER 1.5", odds:107, tier:"VALUE_TB", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.591},
    ],
    parlays: [],
  },
  {
    date: "2026-08-26",
    sport: "MLB",
    plays: [
      {player:"Jesus Luzardo", prop:"K OVER 7.5", odds:114, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.666},
      {player:"Andrew Vaughn", prop:"H OVER 0.5", odds:-199, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.916},
      {player:"Brett Bateman", prop:"TB OVER 1.5", odds:145, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.471},
      {player:"Bryce Harper", prop:"H OVER 0.5", odds:-209, tier:"AUTO", hit:true, actual:6, note:"6 hits — WIN", hit_prob:0.839},
      {player:"Carson Benge", prop:"H OVER 0.5", odds:-209, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.851},
      {player:"Elly De La Cruz", prop:"H OVER 0.5", odds:-202, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.842},
      {player:"Hunter Feduccia", prop:"H OVER 0.5", odds:-107, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.718},
      {player:"Jonny Deluca", prop:"H OVER 0.5", odds:-163, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.854},
      {player:"Junior Caminero", prop:"H OVER 0.5", odds:-197, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.944},
      {player:"Kyle Isbel", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.851},
      {player:"Luis Lara", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.851},
      {player:"Mauricio Dubon", prop:"H OVER 0.5", odds:-207, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.878},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.888},
      {player:"Nathan Church", prop:"H OVER 0.5", odds:-172, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.857},
      {player:"William Contreras", prop:"TB OVER 1.5", odds:136, tier:"VALUE_TB", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.591},
      {player:"Wyatt Langford", prop:"TB OVER 1.5", odds:127, tier:"VALUE_TB", hit:true, actual:null, note:">=2 TB TB — WIN", hit_prob:0.508},
      {player:"Xavier Edwards", prop:"H OVER 0.5", odds:-233, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.87},
      {player:"Zach Neto", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.922},
    ],
    parlays: [],
  },
  {
    date: "2026-08-20",
    sport: "MLB",
    plays: [
      {player:"Grayson Rodriguez", prop:"K OVER 4.5", odds:-111, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.659},
      {player:"Alejandro Kirk", prop:"H OVER 0.5", odds:-221, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.894},
      {player:"Dane Myers", prop:"H OVER 0.5", odds:-172, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.834},
      {player:"Dominic Canzone", prop:"H OVER 0.5", odds:-181, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.866},
      {player:"Jordan Walker", prop:"H OVER 0.5", odds:-243, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.859},
      {player:"Jose Altuve", prop:"H OVER 0.5", odds:-220, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.847},
      {player:"Josh Naylor", prop:"H OVER 0.5", odds:-192, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.931},
      {player:"Kazuma Okamoto", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.829},
      {player:"Michael Massey", prop:"H OVER 0.5", odds:-193, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.854},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-221, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.888},
      {player:"Pete Alonso", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.947},
    ],
    parlays: [],
  },
  {
    date: "2026-08-14",
    sport: "MLB",
    plays: [
      {player:"Bubba Chandler", prop:"K OVER 4.5", odds:110, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.658},
      {player:"Gerrit Cole", prop:"K OVER 5.5", odds:115, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.68},
      {player:"Abimelec Ortiz", prop:"H OVER 0.5", odds:-187, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.826},
      {player:"Angel Martinez", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.916},
      {player:"Chandler Simpson", prop:"TB OVER 1.5", odds:125, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.709},
      {player:"Chase DeLauter", prop:"TB OVER 1.5", odds:139, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.521},
      {player:"Chase Meidroth", prop:"H OVER 0.5", odds:-159, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.829},
      {player:"Gabriel Moreno", prop:"H OVER 0.5", odds:-186, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.878},
      {player:"Gary Sanchez", prop:"H OVER 0.5", odds:-114, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.65},
      {player:"Jackson Merrill", prop:"H OVER 0.5", odds:-184, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.916},
      {player:"Pete Alonso", prop:"H OVER 0.5", odds:-192, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.854},
      {player:"Ronny Simon", prop:"H OVER 0.5", odds:-212, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.827},
      {player:"Sal Stewart", prop:"H OVER 0.5", odds:-244, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.909},
      {player:"Spencer Torkelson", prop:"H OVER 0.5", odds:-184, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.919},
      {player:"Trent Grisham", prop:"H OVER 0.5", odds:-211, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.826},
      {player:"Vladimir Guerrero Jr.", prop:"H OVER 0.5", odds:-236, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.826},
      {player:"Wade Meckler", prop:"H OVER 0.5", odds:-231, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.882},
    ],
    parlays: [],
  },
  {
    date: "2026-08-12",
    sport: "MLB",
    plays: [
      {player:"Chandler Simpson", prop:"H OVER 1.5", odds:170, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.7},
      {player:"Angel Martinez", prop:"H OVER 0.5", odds:-218, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.869},
      {player:"Brandon Nimmo", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.922},
      {player:"Colton Cowser", prop:"H OVER 0.5", odds:-114, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.684},
      {player:"Francisco Lindor", prop:"H OVER 0.5", odds:-192, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.863},
      {player:"Freddy Fermin", prop:"H OVER 0.5", odds:-157, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.907},
      {player:"Jac Caglianone", prop:"H OVER 0.5", odds:-207, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"Jackson Merrill", prop:"H OVER 0.5", odds:-201, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.867},
      {player:"Javier Sanoja", prop:"H OVER 0.5", odds:-212, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.91},
      {player:"Kevin McGonigle", prop:"H OVER 0.5", odds:-226, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.829},
      {player:"Kyle Schwarber", prop:"H OVER 0.5", odds:-193, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.807},
      {player:"Masyn Winn", prop:"H OVER 0.5", odds:-161, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.832},
      {player:"Spencer Torkelson", prop:"H OVER 0.5", odds:-193, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.879},
      {player:"Steven Kwan", prop:"H OVER 0.5", odds:-242, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.944},
      {player:"Tyler Soderstrom", prop:"H OVER 0.5", odds:-183, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.91},
    ],
    parlays: [],
  },
  {
    date: "2026-08-11",
    sport: "MLB",
    plays: [
      {player:"Nolan McLean", prop:"K OVER 5.5", odds:-158, tier:"AUTO", hit:false, actual:3, note:"3 Ks — LOSS", hit_prob:0.943},
      {player:"Patrick Sandoval", prop:"K OVER 4.5", odds:122, tier:"T1", hit:false, actual:4, note:"4 Ks — LOSS", hit_prob:0.705},
      {player:"Andres Gimenez", prop:"H OVER 0.5", odds:-151, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.826},
      {player:"Austin Wells", prop:"H OVER 0.5", odds:105, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.699},
      {player:"Brandon Nimmo", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.857},
      {player:"Ivan Herrera", prop:"H OVER 0.5", odds:-236, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.832},
      {player:"Jac Caglianone", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.925},
      {player:"Jackson Merrill", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.867},
      {player:"Justin Crawford", prop:"H OVER 0.5", odds:-220, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.882},
      {player:"Mauricio Dubon", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.863},
      {player:"Steven Kwan", prop:"H OVER 0.5", odds:-239, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.919},
      {player:"Tyler Soderstrom", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.91},
    ],
    parlays: [],
  },
  {
    date: "2026-08-10",
    sport: "MLB",
    plays: [
      {player:"Christian Scott", prop:"K OVER 5.5", odds:-108, tier:"T1", hit:true, actual:6, note:"6 Ks — WIN", hit_prob:0.748},
      {player:"Brandon Nimmo", prop:"H OVER 0.5", odds:-243, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.832},
      {player:"Bryson Stott", prop:"TB OVER 1.5", odds:155, tier:"VALUE_TB", hit:true, actual:null, note:">=2 TB TB — WIN", hit_prob:0.477},
      {player:"Carson Benge", prop:"H OVER 0.5", odds:-236, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.888},
      {player:"Fernando Tatis Jr.", prop:"H OVER 0.5", odds:-245, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.842},
      {player:"Hunter Feduccia", prop:"H OVER 0.5", odds:100, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.675},
      {player:"Jac Caglianone", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.925},
      {player:"Kyle Tucker", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.9},
      {player:"Tim Tawa", prop:"H OVER 0.5", odds:-186, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.841},
      {player:"Tyler Soderstrom", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.885},
    ],
    parlays: [],
  },
  {
    date: "2026-08-06",
    sport: "MLB",
    plays: [
      {player:"Brandon Young", prop:"K OVER 4.5", odds:-165, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.914},
      {player:"Andruw Monasterio", prop:"H OVER 0.5", odds:-182, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.94},
      {player:"Austin Riley", prop:"H OVER 0.5", odds:-212, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.813},
      {player:"Dillon Dingler", prop:"H OVER 0.5", odds:-214, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.839},
      {player:"Geraldo Perdomo", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.891},
      {player:"Jake Bauers", prop:"H OVER 0.5", odds:-157, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.931},
      {player:"Jarren Duran", prop:"H OVER 0.5", odds:-233, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.85},
      {player:"Royce Lewis", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.944},
      {player:"Steven Kwan", prop:"H OVER 0.5", odds:-233, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.876},
    ],
    parlays: [],
  },
  {
    date: "2026-08-04",
    sport: "MLB",
    plays: [
      {player:"Alec Burleson", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.869},
      {player:"Andruw Monasterio", prop:"H OVER 0.5", odds:-199, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.9},
      {player:"Blaze Jordan", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.844},
      {player:"Carson Kelly", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.81},
      {player:"Christian Walker", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.937},
      {player:"Cole Carrigg", prop:"TB OVER 1.5", odds:131, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.534},
      {player:"Cole Young", prop:"H OVER 0.5", odds:-220, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.904},
      {player:"Dane Myers", prop:"H OVER 0.5", odds:-154, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.924},
      {player:"Endy Rodriguez", prop:"H OVER 0.5", odds:-104, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.656},
      {player:"George Springer", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.937},
      {player:"James McCann", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.931},
      {player:"Kyle Karros", prop:"TB OVER 1.5", odds:124, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.679},
      {player:"Luis Campusano", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.841},
      {player:"Munetaka Murakami", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"Ozzie Albies", prop:"H OVER 0.5", odds:-242, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.863},
      {player:"Tyler Stephenson", prop:"H OVER 0.5", odds:-197, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.859},
      {player:"Willi Castro", prop:"H OVER 0.5", odds:-173, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.914},
    ],
    parlays: [],
  },
  {
    date: "2026-07-30",
    sport: "MLB",
    plays: [
      {player:"Nolan McLean", prop:"K OVER 6.5", odds:-107, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.706},
      {player:"Daylen Lile", prop:"H OVER 0.5", odds:-213, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.838},
      {player:"Freddie Freeman", prop:"H OVER 0.5", odds:-236, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.925},
      {player:"Manny Machado", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.842},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.838},
      {player:"Nick Loftin", prop:"H OVER 0.5", odds:-188, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.919},
      {player:"Ryan Jeffers", prop:"H OVER 0.5", odds:-243, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.879},
      {player:"Ty France", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.867},
      {player:"Willy Adames", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.817},
    ],
    parlays: [],
  },
  {
    date: "2026-07-28",
    sport: "MLB",
    plays: [
      {player:"Cade Cavalli", prop:"K OVER 4.5", odds:113, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.732},
      {player:"Christian Scott", prop:"K OVER 4.5", odds:-150, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"Andruw Monasterio", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.91},
      {player:"Bo Bichette", prop:"TB OVER 1.5", odds:142, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.496},
      {player:"Chandler Simpson", prop:"TB OVER 1.5", odds:131, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.524},
      {player:"Drake Baldwin", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.851},
      {player:"Ezequiel Duran", prop:"H OVER 0.5", odds:-212, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.894},
      {player:"Hao-Yu Lee", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.944},
      {player:"Hunter Goodman", prop:"H OVER 0.5", odds:-164, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.842},
      {player:"Jackson Merrill", prop:"TB OVER 1.5", odds:130, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.487},
      {player:"Jeremy Pena", prop:"H OVER 0.5", odds:-265, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.922},
      {player:"Joc Pederson", prop:"H OVER 0.5", odds:-172, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.919},
      {player:"Kyle Schwarber", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.82},
      {player:"Luis Rengifo", prop:"H OVER 0.5", odds:-211, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.907},
      {player:"Michael Harris II", prop:"H OVER 0.5", odds:-238, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.876},
      {player:"Nick Gonzales", prop:"H OVER 0.5", odds:-250, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.938},
      {player:"Nick Loftin", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.894},
      {player:"Pedro Ramirez", prop:"H OVER 0.5", odds:-219, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.872},
      {player:"Randy Arozarena", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.835},
      {player:"Steven Kwan", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.909},
      {player:"Teoscar Hernandez", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.835},
      {player:"Ty France", prop:"TB OVER 1.5", odds:125, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.537},
      {player:"Tyler Soderstrom", prop:"H OVER 0.5", odds:-224, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.935},
    ],
    parlays: [],
  },
  {
    date: "2026-07-25",
    sport: "MLB",
    plays: [
      {player:"Hunter Greene", prop:"K OVER 6.5", odds:102, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.922},
      {player:"Cody Bellinger", prop:"H OVER 0.5", odds:-209, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.903},
      {player:"Corbin Carroll", prop:"H OVER 0.5", odds:-222, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.807},
      {player:"Edwin Arroyo", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.832},
      {player:"Francisco Alvarez", prop:"H OVER 0.5", odds:-110, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.691},
      {player:"Heriberto Hernandez", prop:"H OVER 0.5", odds:-240, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.87},
      {player:"Ildemaro Vargas", prop:"H OVER 0.5", odds:-208, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.857},
      {player:"J.T. Realmuto", prop:"H OVER 0.5", odds:-191, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.943},
      {player:"Jake McCarthy", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"James McCann", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.832},
      {player:"Jared Triolo", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.863},
      {player:"Jasson Domínguez", prop:"H OVER 0.5", odds:-205, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.878},
      {player:"Jeremy Pena", prop:"H OVER 0.5", odds:-242, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.888},
      {player:"Joc Pederson", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.816},
      {player:"Jonah Heim", prop:"H OVER 0.5", odds:-239, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.854},
      {player:"Julio Rodriguez", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.866},
      {player:"Michael Massey", prop:"H OVER 0.5", odds:-185, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.854},
      {player:"Nick Loftin", prop:"H OVER 0.5", odds:-172, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.804},
      {player:"Steven Kwan", prop:"TB OVER 1.5", odds:135, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.524},
      {player:"Ty France", prop:"H OVER 0.5", odds:-167, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.71},
      {player:"Willson Contreras", prop:"H OVER 0.5", odds:-188, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.875},
      {player:"Yordan Alvarez", prop:"H OVER 0.5", odds:-239, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"Zach Neto", prop:"H OVER 0.5", odds:-220, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.842},
    ],
    parlays: [],
  },
  {
    date: "2026-07-21",
    sport: "MLB",
    plays: [
      {player:"Jack Perkins", prop:"K OVER 4.5", odds:-102, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.754},
      {player:"Ben Rice", prop:"H OVER 0.5", odds:-246, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"Braden Montgomery", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.841},
      {player:"Ceddanne Rafaela", prop:"H OVER 0.5", odds:-248, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.94},
      {player:"Esmerlyn Valdez", prop:"H OVER 0.5", odds:-169, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.934},
      {player:"Hao-Yu Lee", prop:"H OVER 0.5", odds:-154, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.81},
      {player:"Isaac Collins", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.854},
      {player:"Isaac Paredes", prop:"H OVER 0.5", odds:-197, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.872},
      {player:"J.T. Realmuto", prop:"H OVER 0.5", odds:-216, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.878},
      {player:"Jazz Chisholm Jr.", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.844},
      {player:"Jordan Walker", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.947},
      {player:"Lane Thomas", prop:"TB OVER 1.5", odds:130, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.569},
      {player:"Luisangel Acuna", prop:"H OVER 0.5", odds:-113, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.696},
      {player:"Michael Busch", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.86},
      {player:"Petey Halpin", prop:"H OVER 0.5", odds:-159, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.826},
      {player:"Salvador Perez", prop:"H OVER 0.5", odds:-214, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.854},
      {player:"Seiya Suzuki", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.925},
      {player:"Shea Langeliers", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.841},
      {player:"Taylor Walls", prop:"H OVER 0.5", odds:-107, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.656},
      {player:"Tommy Edman", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.943},
      {player:"Ty France", prop:"H OVER 0.5", odds:-233, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.903},
    ],
    parlays: [],
  },
  {
    date: "2026-07-19",
    sport: "MLB",
    plays: [
      {player:"Brandon Young", prop:"K OVER 4.5", odds:-118, tier:"T1", hit:true, actual:7, note:"7 Ks — WIN", hit_prob:0.683},
      {player:"Noah Cameron", prop:"K OVER 4.5", odds:-115, tier:"T1", hit:false, actual:1, note:"1 Ks — LOSS", hit_prob:0.676},
      {player:"Gabriel Moreno", prop:"H OVER 1.5", odds:184, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.681},
      {player:"Ben Rice", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.934},
      {player:"Christian Yelich", prop:"H OVER 0.5", odds:-172, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.841},
      {player:"Cody Bellinger", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.869},
      {player:"Esmerlyn Valdez", prop:"H OVER 0.5", odds:-153, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.851},
      {player:"Ryan Jeffers", prop:"H OVER 0.5", odds:-197, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.9},
      {player:"Seiya Suzuki", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.875},
      {player:"Steven Kwan", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.851},
      {player:"Tommy Edman", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.819},
      {player:"Ty France", prop:"H OVER 0.5", odds:-231, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.829},
    ],
    parlays: [],
  },
  {
    date: "2026-07-17",
    sport: "MLB",
    plays: [
      {player:"Brayan Rocchio", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.876},
      {player:"CJ Abrams", prop:"H OVER 0.5", odds:-207, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.91},
      {player:"Garrett Mitchell", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.866},
      {player:"Jac Caglianone", prop:"H OVER 0.5", odds:-231, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.894},
      {player:"Jonathan Aranda", prop:"H OVER 0.5", odds:-228, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.85},
      {player:"Josh Naylor", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.879},
      {player:"Nolan Schanuel", prop:"H OVER 0.5", odds:-223, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.832},
      {player:"Tommy Edman", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.819},
      {player:"Wyatt Langford", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.928},
      {player:"Xavier Edwards", prop:"H OVER 0.5", odds:-186, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.906},
      {player:"Yainer Diaz", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.847},
    ],
    parlays: [],
  },
  {
    date: "2026-07-12",
    sport: "MLB",
    plays: [
      {player:"Curtis Mead", prop:"TB OVER 1.5", odds:145, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.477},
      {player:"Elly De La Cruz", prop:"TB OVER 1.5", odds:115, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.529},
      {player:"Gabriel Moreno", prop:"H OVER 0.5", odds:-220, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.885},
      {player:"JJ Bleday", prop:"H OVER 0.5", odds:-173, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.884},
      {player:"Jac Caglianone", prop:"H OVER 0.5", odds:-219, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.857},
      {player:"Jasson Domínguez", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.832},
      {player:"Jordan Walker", prop:"H OVER 0.5", odds:-206, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.882},
      {player:"Josh Naylor", prop:"H OVER 0.5", odds:-211, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.894},
      {player:"Kevin McGonigle", prop:"H OVER 0.5", odds:-185, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.879},
      {player:"Michael Massey", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.832},
      {player:"Tyler Stephenson", prop:"H OVER 0.5", odds:-173, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.909},
      {player:"Wyatt Langford", prop:"H OVER 0.5", odds:-199, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.931},
      {player:"Xavier Edwards", prop:"H OVER 0.5", odds:-227, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.86},
      {player:"Yainer Diaz", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.841},
    ],
    parlays: [],
  },
  {
    date: "2026-07-11",
    sport: "MLB",
    plays: [
      {player:"Braxton Ashcraft", prop:"K OVER 6.5", odds:124, tier:"T1", hit:false, actual:6, note:"6 Ks — LOSS", hit_prob:0.708},
      {player:"Peter Lambert", prop:"K OVER 4.5", odds:-117, tier:"T1", hit:true, actual:7, note:"7 Ks — WIN", hit_prob:0.671},
      {player:"CJ Abrams", prop:"H OVER 0.5", odds:-167, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.857},
      {player:"Carson Benge", prop:"H OVER 0.5", odds:-181, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.876},
      {player:"Chase DeLauter", prop:"H OVER 0.5", odds:-196, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.87},
      {player:"Dansby Swanson", prop:"H OVER 0.5", odds:-181, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.884},
      {player:"Gabriel Moreno", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.885},
      {player:"George Springer", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.817},
      {player:"Jac Caglianone", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.832},
      {player:"Jordan Walker", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.882},
      {player:"Josh Naylor", prop:"H OVER 0.5", odds:-216, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.829},
      {player:"Kevin McGonigle", prop:"H OVER 0.5", odds:-232, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.879},
      {player:"Masataka Yoshida", prop:"H OVER 0.5", odds:-204, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.826},
      {player:"Michael Massey", prop:"H OVER 0.5", odds:-169, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.807},
      {player:"Tommy Troy", prop:"H OVER 0.5", odds:-110, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.69},
      {player:"Vinnie Pasquantino", prop:"H OVER 0.5", odds:-203, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.922},
      {player:"Wyatt Langford", prop:"H OVER 0.5", odds:-218, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.891},
      {player:"Xavier Edwards", prop:"H OVER 0.5", odds:-237, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.82},
    ],
    parlays: [],
  },
  {
    date: "2026-07-08",
    sport: "MLB",
    plays: [
      {player:"Dylan Cease", prop:"K OVER 6.5", odds:-164, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"Walbert Urena", prop:"K OVER 4.5", odds:-108, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.721},
      {player:"Michael Harris II", prop:"H OVER 1.5", odds:165, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.773},
      {player:"Otto Lopez", prop:"TB OVER 1.5", odds:115, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.585},
      {player:"Brandon Lowe", prop:"H OVER 0.5", odds:-245, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.823},
      {player:"Brett Baty", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.866},
      {player:"Bryce Eldridge", prop:"H OVER 0.5", odds:-113, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.682},
      {player:"Ceddanne Rafaela", prop:"H OVER 0.5", odds:-218, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.838},
      {player:"Curtis Mead", prop:"H OVER 0.5", odds:-214, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.857},
      {player:"Gabriel Rincones Jr.", prop:"H OVER 0.5", odds:-115, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.674},
      {player:"Heliot Ramos", prop:"H OVER 0.5", odds:-185, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.867},
      {player:"Juan Soto", prop:"H OVER 0.5", odds:-211, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.851},
      {player:"Liam Hicks", prop:"H OVER 0.5", odds:-260, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.935},
      {player:"Luke Keaschall", prop:"H OVER 0.5", odds:-173, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.829},
      {player:"Matt Olson", prop:"H OVER 0.5", odds:-217, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.823},
      {player:"Romy Gonzalez", prop:"H OVER 0.5", odds:-191, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.871},
      {player:"Victor Bericoto", prop:"H OVER 0.5", odds:102, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.707},
      {player:"Willson Contreras", prop:"H OVER 0.5", odds:-194, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.888},
    ],
    parlays: [],
  },
  {
    date: "2026-07-07",
    sport: "MLB",
    plays: [
      {player:"Andrew Alvarez", prop:"K OVER 4.5", odds:-111, tier:"T1", hit:false, actual:3, note:"3 Ks — LOSS", hit_prob:0.757},
      {player:"Brandon Lowe", prop:"H OVER 0.5", odds:-221, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.823},
      {player:"Brayan Rocchio", prop:"H OVER 0.5", odds:-196, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.879},
      {player:"Bryan Reynolds", prop:"H OVER 0.5", odds:-228, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.848},
      {player:"Bryson Stott", prop:"H OVER 0.5", odds:-197, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.949},
      {player:"Chandler Simpson", prop:"H OVER 0.5", odds:-244, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.919},
      {player:"Gavin Sheets", prop:"H OVER 0.5", odds:-170, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.882},
      {player:"Jake Mangum", prop:"TB OVER 1.5", odds:165, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.443},
      {player:"Jake McCarthy", prop:"H OVER 0.5", odds:-173, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.835},
      {player:"Liam Hicks", prop:"H OVER 0.5", odds:-254, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.935},
      {player:"Michael Harris II", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.823},
      {player:"Nick Gonzales", prop:"H OVER 0.5", odds:-230, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.848},
      {player:"Otto Lopez", prop:"H OVER 0.5", odds:-265, tier:"AUTO", hit:false, actual:1, note:"1 hits — LOSS", hit_prob:0.845},
      {player:"Steven Kwan", prop:"H OVER 0.5", odds:-178, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.919},
      {player:"Victor Bericoto", prop:"H OVER 0.5", odds:-110, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.682},
    ],
    parlays: [],
  },
  {
    date: "2026-07-02",
    sport: "MLB",
    plays: [
      {player:"Trea Turner", prop:"TB OVER 1.5", odds:100, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.573},
      {player:"Cole Young", prop:"H OVER 0.5", odds:-162, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.839},
      {player:"Esmerlyn Valdez", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.878},
      {player:"Jake Mangum", prop:"TB OVER 1.5", odds:155, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.448},
      {player:"Julio Rodriguez", prop:"H OVER 0.5", odds:-242, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.879},
      {player:"Justin Crawford", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.853},
      {player:"Kerry Carpenter", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.841},
      {player:"Mookie Betts", prop:"H OVER 0.5", odds:-227, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.925},
      {player:"Sal Frelick", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.841},
      {player:"Sal Stewart", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.906},
      {player:"Tyler Stephenson", prop:"H OVER 0.5", odds:-115, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.746},
    ],
    parlays: [],
  },
  {
    date: "2026-06-28",
    sport: "MLB",
    plays: [
      {player:"Brady Singer", prop:"K OVER 4.5", odds:-118, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.708},
      {player:"Bo Bichette", prop:"H OVER 0.5", odds:-242, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.851},
      {player:"Bryan Reynolds", prop:"H OVER 0.5", odds:-246, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.938},
      {player:"Bryce Harper", prop:"TB OVER 1.5", odds:115, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.521},
      {player:"Freddie Freeman", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.842},
      {player:"Gabriel Moreno", prop:"H OVER 0.5", odds:-180, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.944},
      {player:"Ian Happ", prop:"H OVER 0.5", odds:-113, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.656},
      {player:"Jake McCarthy", prop:"H OVER 0.5", odds:-218, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.944},
      {player:"Konnor Griffin", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.823},
      {player:"Kyle Stowers", prop:"H OVER 0.5", odds:-220, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.832},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-216, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.838},
      {player:"TJ Rumfield", prop:"H OVER 0.5", odds:-203, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.944},
      {player:"Trea Turner", prop:"TB OVER 1.5", odds:124, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.591},
      {player:"Trevor Larnach", prop:"TB OVER 1.5", odds:130, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.524},
    ],
    parlays: [],
  },
  {
    date: "2026-06-26",
    sport: "MLB",
    plays: [
      {player:"Max Meyer", prop:"K OVER 5.5", odds:-106, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.702},
      {player:"Brandon Lowe", prop:"H OVER 0.5", odds:-188, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.913},
      {player:"Carter Jensen", prop:"H OVER 0.5", odds:-184, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"Cole Carrigg", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.829},
      {player:"Donovan Walton", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.922},
      {player:"Gabriel Moreno", prop:"H OVER 0.5", odds:-232, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.919},
      {player:"Jake McCarthy", prop:"H OVER 0.5", odds:-203, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.944},
      {player:"Masyn Winn", prop:"H OVER 0.5", odds:-185, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.897},
      {player:"Royce Lewis", prop:"H OVER 0.5", odds:-217, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.854},
      {player:"TJ Rumfield", prop:"H OVER 0.5", odds:-215, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.919},
    ],
    parlays: [],
  },
  {
    date: "2026-06-24",
    sport: "MLB",
    plays: [
      {player:"Brandon Lowe", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.888},
      {player:"Brandon Nimmo", prop:"H OVER 0.5", odds:-203, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.885},
      {player:"Brice Turang", prop:"TB OVER 1.5", odds:135, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.504},
      {player:"Bryan Reynolds", prop:"H OVER 0.5", odds:-228, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.938},
      {player:"Byron Buxton", prop:"H OVER 0.5", odds:-171, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.879},
      {player:"Dillon Dingler", prop:"TB OVER 1.5", odds:110, tier:"VALUE_TB", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.594},
      {player:"Donovan Walton", prop:"H OVER 0.5", odds:-178, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.897},
      {player:"Isaac Paredes", prop:"H OVER 0.5", odds:-161, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.891},
      {player:"Jake McCarthy", prop:"H OVER 0.5", odds:-242, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.95},
      {player:"Jonathan Aranda", prop:"H OVER 0.5", odds:-198, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.854},
      {player:"Masyn Winn", prop:"H OVER 0.5", odds:-185, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.897},
      {player:"Michael Harris II", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.907},
      {player:"Nick Gonzales", prop:"TB OVER 1.5", odds:150, tier:"VALUE_TB", hit:true, actual:null, note:">=2 TB TB — WIN", hit_prob:0.468},
      {player:"Nolan Schanuel", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.832},
      {player:"Otto Lopez", prop:"H OVER 0.5", odds:-239, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.845},
      {player:"Tyler Stephenson", prop:"H OVER 0.5", odds:-118, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.699},
      {player:"Zach Neto", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.832},
    ],
    parlays: [],
  },
  {
    date: "2026-06-23",
    sport: "MLB",
    plays: [
      {player:"Caleb Durbin", prop:"H OVER 1.5", odds:164, tier:"T1", hit:false, actual:1, note:"1 hits — LOSS", hit_prob:0.719},
      {player:"Josh Jung", prop:"TB OVER 1.5", odds:117, tier:"VALUE_TB", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.535},
      {player:"Yandy Diaz", prop:"TB OVER 1.5", odds:103, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.544},
      {player:"Blake Perkins", prop:"H OVER 0.5", odds:-167, tier:"AUTO", hit:"void", actual:0, note:"DNP / not in box scores — VOID", hit_prob:0.834},
      {player:"Brandon Lowe", prop:"H OVER 0.5", odds:-228, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.848},
      {player:"Brandon Nimmo", prop:"H OVER 0.5", odds:-218, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.82},
      {player:"Brandon Valenzuela", prop:"H OVER 0.5", odds:-173, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.876},
      {player:"Bryan Reynolds", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.938},
      {player:"CJ Abrams", prop:"H OVER 0.5", odds:-170, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.857},
      {player:"Carter Jensen", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.944},
      {player:"Casey Schmitt", prop:"H OVER 0.5", odds:-233, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.882},
      {player:"Donovan Walton", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:"void", actual:0, note:"DNP / not in box scores — VOID", hit_prob:0.897},
      {player:"Henry Bolte", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.867},
      {player:"Isaac Paredes", prop:"H OVER 0.5", odds:-182, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.866},
      {player:"JJ Wetherholt", prop:"TB OVER 1.5", odds:135, tier:"VALUE_TB", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.527},
      {player:"Jake Mangum", prop:"H OVER 0.5", odds:-219, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.913},
      {player:"Jonathan Aranda", prop:"H OVER 0.5", odds:-217, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.854},
      {player:"Juan Soto", prop:"H OVER 0.5", odds:-222, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.876},
      {player:"Kameron Misner", prop:"H OVER 0.5", odds:-105, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.652},
      {player:"Keibert Ruiz", prop:"H OVER 0.5", odds:-174, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.882},
      {player:"Kevin McGonigle", prop:"H OVER 0.5", odds:-194, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.919},
      {player:"Lane Thomas", prop:"H OVER 0.5", odds:-167, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.894},
      {player:"Luisangel Acuna", prop:"H OVER 0.5", odds:-115, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.718},
      {player:"Masyn Winn", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.897},
      {player:"Michael Harris II", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.907},
      {player:"Nathan Church", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.857},
      {player:"Nolan Schanuel", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.832},
      {player:"Travis Bazzana", prop:"H OVER 0.5", odds:-220, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.863},
      {player:"Wyatt Langford", prop:"TB OVER 1.5", odds:120, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.585},
      {player:"Zack Gelof", prop:"H OVER 0.5", odds:-181, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.932},
    ],
    parlays: [],
  },
  {
    date: "2026-06-20",
    sport: "MLB",
    plays: [
      {player:"Cade Cavalli", prop:"K OVER 4.5", odds:-108, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.73},
      {player:"Alec Bohm", prop:"TB OVER 1.5", odds:139, tier:"VALUE_TB", hit:null, actual:null, note:"Pending", hit_prob:0.498},
      {player:"Casey Schmitt", prop:"H OVER 0.5", odds:-189, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.82},
      {player:"Cooper Pratt", prop:"H OVER 0.5", odds:-107, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.66},
      {player:"Donovan Walton", prop:"H OVER 0.5", odds:-182, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.82},
      {player:"Gabriel Moreno", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.891},
      {player:"Isiah Kiner-Falefa", prop:"H OVER 0.5", odds:-171, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.814},
      {player:"Jake Burger", prop:"H OVER 0.5", odds:-163, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.891},
      {player:"Jake McCarthy", prop:"H OVER 0.5", odds:-244, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.95},
      {player:"Josh Bell", prop:"H OVER 0.5", odds:-207, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.891},
      {player:"Kyle Tucker", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.86},
      {player:"Liam Hicks", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.935},
      {player:"Mauricio Dubon", prop:"H OVER 0.5", odds:-228, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.928},
      {player:"Zack Gelof", prop:"H OVER 0.5", odds:-249, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.935},
    ],
    parlays: [],
  },
  {
    date: "2026-06-18",
    sport: "MLB",
    plays: [
      {player:"Bryce Eldridge", prop:"H OVER 0.5", odds:-185, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.928},
      {player:"Byron Buxton", prop:"H OVER 0.5", odds:-229, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.866},
      {player:"Carter Jensen", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.919},
      {player:"Denzer Guzman", prop:"H OVER 0.5", odds:-196, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.832},
      {player:"Dominic Canzone", prop:"H OVER 0.5", odds:-176, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.879},
      {player:"Elias Diaz", prop:"H OVER 0.5", odds:105, tier:"T1", hit:null, actual:null, note:"Pending", hit_prob:0.681},
      {player:"Isiah Kiner-Falefa", prop:"H OVER 0.5", odds:-199, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.825},
      {player:"Logan O'Hoppe", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.885},
      {player:"Matt Olson", prop:"H OVER 0.5", odds:-191, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.928},
      {player:"Mauricio Dubon", prop:"H OVER 0.5", odds:-223, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.928},
      {player:"Mike Trout", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.885},
      {player:"Nick Kurtz", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.935},
      {player:"Paul Goldschmidt", prop:"H OVER 0.5", odds:-215, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.934},
      {player:"Zack Gelof", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:null, actual:null, note:"Pending", hit_prob:0.935},
    ],
    parlays: [],
  },
  {
    date: "2026-06-17",
    sport: "MLB",
    plays: [
      {player:"Bryce Eldridge", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.928},
      {player:"Dominic Canzone", prop:"H OVER 0.5", odds:-170, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.839},
      {player:"Jarren Duran", prop:"H OVER 0.5", odds:-220, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.85},
      {player:"Matt Olson", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.863},
      {player:"Nick Kurtz", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.91},
      {player:"Zack Gelof", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.935},
    ],
    parlays: [],
  },
  {
    date: "2026-06-16",
    sport: "MLB",
    plays: [
      {player:"Reid Detmers", prop:"K OVER 4.5", odds:-161, tier:"AUTO", hit:false, actual:3, note:"3 Ks — LOSS", hit_prob:0.941},
      {player:"Bo Bichette", prop:"H OVER 1.5", odds:155, tier:"T1", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.714},
      {player:"Alex Bregman", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.81},
      {player:"Austin Hedges", prop:"H OVER 0.5", odds:-117, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.746},
      {player:"Bryce Eldridge", prop:"H OVER 0.5", odds:-228, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.888},
      {player:"Cole Young", prop:"H OVER 0.5", odds:-162, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.864},
      {player:"Dillon Dingler", prop:"TB OVER 1.5", odds:139, tier:"VALUE_TB", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.517},
      {player:"Dylan Crews", prop:"H OVER 0.5", odds:-213, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.807},
      {player:"Henry Bolte", prop:"H OVER 0.5", odds:-192, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.885},
      {player:"Jake McCarthy", prop:"H OVER 0.5", odds:-230, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.86},
      {player:"James Wood", prop:"H OVER 0.5", odds:-234, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.922},
      {player:"Jo Adell", prop:"TB OVER 1.5", odds:120, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.511},
      {player:"Kyle Schwarber", prop:"H OVER 0.5", odds:-188, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.853},
      {player:"Logan O'Hoppe", prop:"H OVER 0.5", odds:-181, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.841},
      {player:"Marcelo Mayer", prop:"H OVER 0.5", odds:-107, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.665},
      {player:"Mauricio Dubon", prop:"H OVER 0.5", odds:-216, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.888},
      {player:"Mike Trout", prop:"H OVER 0.5", odds:-239, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.816},
      {player:"Nasim Nunez", prop:"H OVER 0.5", odds:-115, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.697},
      {player:"Paul Goldschmidt", prop:"H OVER 0.5", odds:-178, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.934},
      {player:"Pete Alonso", prop:"H OVER 0.5", odds:-185, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.839},
      {player:"Samad Taylor", prop:"H OVER 0.5", odds:-162, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.916},
      {player:"Willi Castro", prop:"TB OVER 1.5", odds:140, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.505},
      {player:"Zack Gelof", prop:"H OVER 0.5", odds:-213, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.935},
    ],
    parlays: [],
  },
  {
    date: "2026-06-15",
    sport: "MLB",
    plays: [
      {player:"Walbert Urena", prop:"K OVER 4.5", odds:118, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.696},
      {player:"Bo Bichette", prop:"H OVER 0.5", odds:-235, tier:"T1", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.764},
      {player:"Henry Bolte", prop:"H OVER 0.5", odds:-180, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.845},
      {player:"JJ Wetherholt", prop:"TB OVER 1.5", odds:145, tier:"VALUE_TB", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.527},
      {player:"Jake Mangum", prop:"TB OVER 1.5", odds:145, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.465},
      {player:"Juan Soto", prop:"TB OVER 1.5", odds:115, tier:"T1", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.664},
      {player:"Liam Hicks", prop:"H OVER 0.5", odds:-180, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.853},
      {player:"Logan O'Hoppe", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.841},
      {player:"Michael Busch", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.925},
      {player:"Nick Kurtz", prop:"H OVER 0.5", odds:-206, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.86},
      {player:"Noelvi Marte", prop:"H OVER 0.5", odds:-219, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.924},
      {player:"Otto Lopez", prop:"H OVER 0.5", odds:-245, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.943},
      {player:"Royce Lewis", prop:"H OVER 0.5", odds:-215, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.906},
      {player:"Samad Taylor", prop:"H OVER 0.5", odds:-168, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.916},
      {player:"Seiya Suzuki", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.95},
      {player:"TJ Rumfield", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.81},
      {player:"Zack Gelof", prop:"H OVER 0.5", odds:-177, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.935},
    ],
    parlays: [],
  },
  {
    date: "2026-06-14",
    sport: "MLB",
    plays: [
      {player:"Cole Young", prop:"TB OVER 1.5", odds:220, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.427},
      {player:"Fernando Tatis Jr.", prop:"TB OVER 2.5", odds:170, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.427},
      {player:"Jung Hoo Lee", prop:"TB OVER 1.5", odds:145, tier:"VALUE_TB", hit:true, actual:null, note:">=2 TB TB — WIN", hit_prob:0.462},
      {player:"Bryce Eldridge", prop:"H OVER 0.5", odds:-182, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.867},
      {player:"Jhonny Pereda", prop:"H OVER 0.5", odds:170, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.672},
      {player:"Jordan Lawlar", prop:"H OVER 0.5", odds:200, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.661},
      {player:"Jordan Walker", prop:"H OVER 0.5", odds:126, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.669},
      {player:"LuJames Groover", prop:"H OVER 0.5", odds:220, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.653},
      {player:"Michael Busch", prop:"H OVER 0.5", odds:-212, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.907},
    ],
    parlays: [],
  },
  {
    date: "2026-06-13",
    sport: "MLB",
    plays: [
      {player:"Tarik Skubal", prop:"K OVER 5.5", odds:-104, tier:"T1", hit:false, actual:4, note:"4 Ks — LOSS", hit_prob:0.68},
      {player:"Angel Martinez", prop:"H OVER 0.5", odds:-193, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.826},
      {player:"Austin Hedges", prop:"H OVER 0.5", odds:110, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.666},
      {player:"Carter Jensen", prop:"H OVER 0.5", odds:-207, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.804},
      {player:"Chase Meidroth", prop:"H OVER 0.5", odds:-192, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.95},
      {player:"Christian Yelich", prop:"TB OVER 1.5", odds:140, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.486},
      {player:"Jhonny Pereda", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.922},
      {player:"Jose Fermin", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.829},
      {player:"Jose Siri", prop:"H OVER 0.5", odds:-103, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.672},
      {player:"Josh Bell", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.854},
      {player:"Michael Busch", prop:"H OVER 0.5", odds:-199, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.867},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-191, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.928},
      {player:"Nathan Lukes", prop:"H OVER 0.5", odds:-191, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.876},
      {player:"Paul Goldschmidt", prop:"H OVER 0.5", odds:-234, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.876},
      {player:"Royce Lewis", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.829},
      {player:"Samad Taylor", prop:"H OVER 0.5", odds:-179, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.865},
      {player:"Seiya Suzuki", prop:"H OVER 0.5", odds:-210, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.907},
      {player:"Shohei Ohtani", prop:"H OVER 0.5", odds:-224, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.888},
      {player:"Taylor Ward", prop:"H OVER 0.5", odds:-221, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.882},
      {player:"Vinnie Pasquantino", prop:"H OVER 0.5", odds:-238, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.894},
      {player:"Yandy Diaz", prop:"H OVER 0.5", odds:-235, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.922},
      {player:"Zack Gelof", prop:"H OVER 0.5", odds:-225, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.935},
    ],
    parlays: [],
  },
  {
    date: "2026-06-12",
    sport: "MLB",
    plays: [
      {player:"Blake Dunn", prop:"H OVER 0.5", odds:-166, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.924},
      {player:"Chase Meidroth", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.95},
      {player:"Dane Myers", prop:"H OVER 0.5", odds:-241, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.859},
      {player:"Jordan Walker", prop:"H OVER 0.5", odds:-228, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.919},
      {player:"Keibert Ruiz", prop:"H OVER 0.5", odds:-166, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.857},
      {player:"Michael Busch", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.867},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.928},
      {player:"Nathan Lukes", prop:"H OVER 0.5", odds:-173, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.876},
      {player:"Seiya Suzuki", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.882},
      {player:"Taylor Ward", prop:"H OVER 0.5", odds:-231, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.857},
      {player:"Trent Grisham", prop:"H OVER 0.5", odds:-173, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.851},
      {player:"Vinnie Pasquantino", prop:"H OVER 0.5", odds:-205, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.854},
    ],
    parlays: [],
  },
  {
    date: "2026-06-11",
    sport: "MLB",
    plays: [
      {player:"Josh Naylor", prop:"TB OVER 1.5", odds:120, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.282},
      {player:"Miguel Vargas", prop:"TB OVER 1.5", odds:107, tier:"SKIP", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.2},
      {player:"Ryan Ward", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.842},
    ],
    parlays: [],
  },
  {
    date: "2026-06-10",
    sport: "MLB",
    plays: [
      {player:"A.J. Ewing", prop:"H OVER 0.5", odds:-182, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.826},
      {player:"Alec Burleson", prop:"TB OVER 1.5", odds:130, tier:"VALUE_TB_SHADOW", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.446},
      {player:"Blake Dunn", prop:"H OVER 0.5", odds:-183, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.882},
      {player:"Chase Meidroth", prop:"H OVER 0.5", odds:-187, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.95},
      {player:"Jordan Walker", prop:"TB OVER 1.5", odds:120, tier:"VALUE_TB", hit:true, actual:2, note:"2 TB — WIN", hit_prob:0.541},
      {player:"Jung Hoo Lee", prop:"TB OVER 1.5", odds:124, tier:"VALUE_TB", hit:true, actual:2, note:"2 TB — WIN", hit_prob:0.512},
      {player:"Kody Clemens", prop:"H OVER 0.5", odds:-199, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.854},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-184, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.928},
      {player:"Randy Arozarena", prop:"TB OVER 1.5", odds:138, tier:"VALUE_TB_SHADOW", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.452},
      {player:"Ryan Vilade", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.829},
      {player:"Tyler Stephenson", prop:"H OVER 0.5", odds:-119, tier:"T1", hit:"void", actual:0, note:"DNP / not in box scores — VOID", hit_prob:0.672},
      {player:"Yohendrick Pinango", prop:"H OVER 0.5", odds:-105, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.706},
      {player:"Zach Neto", prop:"TB OVER 1.5", odds:120, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.2},
      {player:"Zack Gelof", prop:"TB OVER 1.5", odds:100, tier:"SKIP", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.2},
    ],
    parlays: [],
  },
  {
    date: "2026-06-09",
    sport: "MLB",
    plays: [
      {player:"Nathan Eovaldi", prop:"K OVER 4.5", odds:-156, tier:"AUTO", hit:false, actual:3, note:"3 Ks — LOSS", hit_prob:0.921},
      {player:"Paul Skenes", prop:"K OVER 6.5", odds:-113, tier:"T1", hit:true, actual:7, note:"7 Ks — WIN", hit_prob:0.683},
      {player:"A.J. Ewing", prop:"H OVER 0.5", odds:-154, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.801},
      {player:"Alec Bohm", prop:"H OVER 0.5", odds:-184, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.851},
      {player:"Alec Burleson", prop:"TB OVER 1.5", odds:130, tier:"VALUE_TB_SHADOW", hit:true, actual:2, note:"2 TB — WIN", hit_prob:0.421},
      {player:"Blake Dunn", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.817},
      {player:"Chase Meidroth", prop:"H OVER 0.5", odds:-203, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.928},
      {player:"Cole Young", prop:"H OVER 0.5", odds:-209, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.947},
      {player:"Ernie Clement", prop:"TB OVER 1.5", odds:145, tier:"VALUE_TB", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.471},
      {player:"Jordan Walker", prop:"H OVER 0.5", odds:-163, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.826},
      {player:"Josh Naylor", prop:"TB OVER 1.5", odds:138, tier:"VALUE_TB", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.477},
      {player:"Kevin McGonigle", prop:"TB OVER 1.5", odds:125, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.279},
      {player:"Kyle Higashioka", prop:"H OVER 0.5", odds:-176, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.829},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-184, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.863},
      {player:"Shohei Ohtani", prop:"TB OVER 1.5", odds:115, tier:"T1", hit:true, actual:2, note:"2 TB — WIN", hit_prob:0.663},
      {player:"Victor Caratini", prop:"H OVER 0.5", odds:-171, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.894},
      {player:"Vinnie Pasquantino", prop:"TB OVER 1.5", odds:120, tier:"VALUE_TB", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.524},
      {player:"Zack Gelof", prop:"TB OVER 1.5", odds:125, tier:"SKIP", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.2},
    ],
    parlays: [],
  },
  {
    date: "2026-06-08",
    sport: "MLB",
    plays: [
      {player:"Connelly Early", prop:"K OVER 4.5", odds:-153, tier:"AUTO", hit:true, actual:6, note:"6 Ks — WIN", hit_prob:0.908},
      {player:"Cristopher Sanchez", prop:"K OVER 6.5", odds:115, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.723},
      {player:"Blake Dunn", prop:"H OVER 0.5", odds:-198, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.817},
      {player:"Brandon Marsh", prop:"TB OVER 1.5", odds:150, tier:"VALUE_TB", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.496},
      {player:"Brandon Valenzuela", prop:"H OVER 0.5", odds:-110, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.706},
      {player:"Jhonny Pereda", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.857},
      {player:"Kazuma Okamoto", prop:"H OVER 0.5", odds:-173, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.851},
    ],
    parlays: [],
  },
  {
    date: "2026-06-07",
    sport: "MLB",
    plays: [
      {player:"Cade Cavalli", prop:"K OVER 4.5", odds:-112, tier:"T1", hit:false, actual:2, note:"2 Ks — LOSS", hit_prob:0.721},
      {player:"Connor Prielipp", prop:"K OVER 4.5", odds:-150, tier:"T1", hit:true, actual:7, note:"7 Ks — WIN", hit_prob:0.69},
      {player:"Jose Soriano", prop:"K OVER 4.5", odds:-156, tier:"T1", hit:false, actual:2, note:"2 Ks — LOSS", hit_prob:0.7},
      {player:"Luis Castillo", prop:"K OVER 4.5", odds:-106, tier:"T1", hit:true, actual:5, note:"5 Ks — WIN", hit_prob:0.698},
      {player:"Shane Baz", prop:"K OVER 4.5", odds:-145, tier:"T1", hit:false, actual:3, note:"3 Ks — LOSS", hit_prob:0.705},
      {player:"Adolis Garcia", prop:"H OVER 0.5", odds:-140, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.803},
      {player:"Alex Jackson", prop:"H OVER 0.5", odds:-115, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.661},
      {player:"Bryce Eldridge", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.925},
      {player:"Caleb Durbin", prop:"H OVER 0.5", odds:-130, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.909},
      {player:"Cole Young", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.919},
      {player:"Drew Millas", prop:"H OVER 0.5", odds:-134, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.721},
      {player:"Isaac Paredes", prop:"TB OVER 1.5", odds:130, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.272},
      {player:"Jacob Gonzalez", prop:"H OVER 0.5", odds:-160, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.766},
      {player:"Jhonny Pereda", prop:"H OVER 0.5", odds:-135, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.854},
      {player:"Kazuma Okamoto", prop:"H OVER 0.5", odds:-140, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.851},
      {player:"Kyle Higashioka", prop:"H OVER 0.5", odds:-120, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.841},
      {player:"Nasim Nunez", prop:"H OVER 0.5", odds:-120, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.681},
      {player:"Pete Alonso", prop:"TB OVER 1.5", odds:130, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.276},
      {player:"Seiya Suzuki", prop:"H OVER 0.5", odds:-185, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.74},
      {player:"Trent Grisham", prop:"H OVER 0.5", odds:-165, tier:"T1", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.684},
      {player:"Tristan Peters", prop:"H OVER 0.5", odds:-175, tier:"T1", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.718},
      {player:"Victor Caratini", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.869},
      {player:"Zack Gelof", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.95},
    ],
    parlays: [],
  },
  {
    date: "2026-06-06",
    sport: "MLB",
    plays: [
      {player:"Ben Brown", prop:"K OVER 4.5", odds:-168, tier:"T1", hit:true, actual:5, note:"5 Ks — WIN", hit_prob:0.764},
      {player:"Jacob Misiorowski", prop:"K OVER 7.5", odds:-149, tier:"AUTO", hit:true, actual:8, note:"8 Ks — WIN", hit_prob:0.917},
      {player:"Joe Ryan", prop:"K OVER 5.5", odds:-161, tier:"T1", hit:false, actual:5, note:"5 Ks — LOSS", hit_prob:0.735},
      {player:"Adolis Garcia", prop:"H OVER 0.5", odds:-140, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.658},
      {player:"Bryce Eldridge", prop:"H OVER 0.5", odds:-139, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.925},
      {player:"Caleb Durbin", prop:"H OVER 0.5", odds:-173, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.909},
      {player:"Coby Mayo", prop:"H OVER 0.5", odds:-145, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.851},
      {player:"Heriberto Hernandez", prop:"H OVER 0.5", odds:-147, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.685},
      {player:"Jac Caglianone", prop:"H OVER 0.5", odds:-165, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.694},
      {player:"Jacob Gonzalez", prop:"H OVER 0.5", odds:-175, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.718},
      {player:"Jhonny Pereda", prop:"H OVER 0.5", odds:-156, tier:"T1", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.709},
      {player:"Jo Adell", prop:"H OVER 0.5", odds:-125, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.675},
      {player:"Kazuma Okamoto", prop:"H OVER 0.5", odds:-154, tier:"T1", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.731},
      {player:"Kyle Karros", prop:"H OVER 0.5", odds:-151, tier:"T1", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.679},
      {player:"Matt Vierling", prop:"H OVER 0.5", odds:-144, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.669},
      {player:"Michael Massey", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.829},
      {player:"Riley Greene", prop:"TB OVER 1.5", odds:125, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.474},
      {player:"Tyler Soderstrom", prop:"H OVER 0.5", odds:-175, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.687},
      {player:"Vaughn Grissom", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.9},
      {player:"Victor Caratini", prop:"H OVER 0.5", odds:-185, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.804},
      {player:"Zack Gelof", prop:"H OVER 0.5", odds:-140, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.95},
    ],
    parlays: [],
  },
  {
    date: "2026-06-05",
    sport: "MLB",
    plays: [
      {player:"Foster Griffin", prop:"K OVER 4.5", odds:108, tier:"AUTO", hit:false, actual:4, note:"4 Ks — LOSS", hit_prob:0.891},
      {player:"Reid Detmers", prop:"K OVER 5.5", odds:118, tier:"T1", hit:true, actual:6, note:"6 Ks — WIN", hit_prob:0.7},
      {player:"Zebby Matthews", prop:"K OVER 4.5", odds:-156, tier:"AUTO", hit:false, actual:2, note:"2 Ks — LOSS", hit_prob:0.887},
      {player:"Caleb Durbin", prop:"H OVER 0.5", odds:-169, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.884},
      {player:"Ceddanne Rafaela", prop:"TB OVER 1.5", odds:135, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.294},
      {player:"Coby Mayo", prop:"H OVER 0.5", odds:-136, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.731},
      {player:"Cole Young", prop:"H OVER 0.5", odds:-168, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.919},
      {player:"Connor Wong", prop:"H OVER 0.5", odds:-121, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.709},
      {player:"Donovan Walton", prop:"H OVER 0.5", odds:-128, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.9},
      {player:"Joe Mack", prop:"H OVER 0.5", odds:-105, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.66},
      {player:"Jung Hoo Lee", prop:"H OVER 0.5", odds:-125, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.95},
      {player:"Kazuma Okamoto", prop:"H OVER 0.5", odds:-169, tier:"T1", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.691},
      {player:"Kyle Stowers", prop:"H OVER 0.5", odds:-179, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.7},
      {player:"Leody Taveras", prop:"H OVER 0.5", odds:-133, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.691},
      {player:"Michael Massey", prop:"H OVER 0.5", odds:-164, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.804},
      {player:"Mickey Gasper", prop:"H OVER 0.5", odds:-133, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.844},
      {player:"Nathan Lukes", prop:"TB OVER 1.5", odds:133, tier:"T1", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.656},
      {player:"Nick Loftin", prop:"H OVER 0.5", odds:-133, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.684},
      {player:"Oneil Cruz", prop:"H OVER 0.5", odds:-155, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.678},
      {player:"Oswald Peraza", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.86},
      {player:"Pete Crow-Armstrong", prop:"H OVER 0.5", odds:-120, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.675},
      {player:"Shohei Ohtani", prop:"TB OVER 1.5", odds:-103, tier:"T1", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.665},
      {player:"Troy Johnston", prop:"TB OVER 1.5", odds:125, tier:"T1", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.694},
      {player:"Vaughn Grissom", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.9},
      {player:"Will Smith", prop:"H OVER 0.5", odds:-160, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.7},
      {player:"Zack Gelof", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.937},
    ],
    parlays: [],
  },
  {
    date: "2026-06-03",
    sport: "MLB",
    plays: [
      {player:"Chase Burns", prop:"K OVER 6.5", odds:-142, tier:"T1", hit:true, actual:9, note:"9 Ks — WIN", hit_prob:0.713},
      {player:"Cristopher Sanchez", prop:"K OVER 6.5", odds:-152, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.658},
      {player:"Max Meyer", prop:"K OVER 5.5", odds:116, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.707},
      {player:"Shohei Ohtani", prop:"TB OVER 1.5", odds:-115, tier:"T2", hit:true, actual:3, note:"3 TB — WIN", hit_prob:0.631},
      {player:"Taj Bradley", prop:"K OVER 5.5", odds:-158, tier:"T1", hit:false, actual:5, note:"5 Ks — LOSS", hit_prob:0.728},
      {player:"Ben Rice", prop:"TB OVER 1.5", odds:128, tier:"SKIP", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.439},
      {player:"Blaze Alexander", prop:"H OVER 0.5", odds:-149, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.69},
      {player:"Bryce Eldridge", prop:"H OVER 0.5", odds:-126, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.841},
      {player:"Caleb Durbin", prop:"H OVER 0.5", odds:-185, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.825},
      {player:"Coby Mayo", prop:"H OVER 0.5", odds:-135, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.715},
      {player:"Cole Young", prop:"H OVER 0.5", odds:-152, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.864},
      {player:"Colt Emerson", prop:"H OVER 0.5", odds:-132, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.669},
      {player:"Donovan Walton", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.891},
      {player:"Hunter Goodman", prop:"H OVER 0.5", odds:-160, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.672},
      {player:"Jake Meyers", prop:"H OVER 0.5", odds:-151, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.702},
      {player:"Jazz Chisholm Jr.", prop:"H OVER 0.5", odds:-161, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.684},
      {player:"Jorge Soler", prop:"H OVER 0.5", odds:-175, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.722},
      {player:"Jung Hoo Lee", prop:"TB OVER 1.5", odds:138, tier:"SKIP", hit:true, actual:2, note:"2 TB — WIN", hit_prob:0.411},
      {player:"Kyle Karros", prop:"H OVER 0.5", odds:-136, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.712},
      {player:"Leody Taveras", prop:"H OVER 0.5", odds:-135, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.665},
      {player:"Michael Busch", prop:"H OVER 0.5", odds:-177, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.74},
      {player:"Michael Massey", prop:"H OVER 0.5", odds:-136, tier:"T1", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.674},
      {player:"Nolan Arenado", prop:"H OVER 0.5", odds:-164, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.681},
      {player:"Oswald Peraza", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.857},
      {player:"Paul Goldschmidt", prop:"H OVER 0.5", odds:-174, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.884},
      {player:"Trent Grisham", prop:"H OVER 0.5", odds:-173, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.709},
      {player:"Tyler Freeman", prop:"H OVER 0.5", odds:-200, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.897},
      {player:"Zack Gelof", prop:"H OVER 0.5", odds:-161, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.9},
    ],
    parlays: [],
  },
  {
    date: "2026-06-01",
    sport: "MLB",
    plays: [
      {player:"Emmet Sheehan", prop:"K OVER 5.5", odds:-102, tier:"SKIP", hit:false, actual:3, note:"3 Ks — LOSS", hit_prob:0.466},
      {player:"Landen Roupp", prop:"K OVER 5.5", odds:-130, tier:"SKIP", hit:false, actual:4, note:"4 Ks — LOSS", hit_prob:0.483},
      {player:"Bryce Eldridge", prop:"H OVER 0.5", odds:-141, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.721},
      {player:"Cole Young", prop:"H OVER 0.5", odds:-135, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.839},
      {player:"Ezequiel Tovar", prop:"H OVER 0.5", odds:-157, tier:"SKIP", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.502},
      {player:"Freddie Freeman", prop:"TB OVER 1.5", odds:103, tier:"SKIP", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.2},
      {player:"J.P. Crawford", prop:"H OVER 0.5", odds:-175, tier:"JUICE", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.604},
      {player:"JJ Wetherholt", prop:"H OVER 0.5", odds:-196, tier:"JUICE", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.622},
    ],
    parlays: [],
  },
  {
    date: "2026-05-26",
    sport: "MLB",
    plays: [
      {player:"Tyler Mahle", prop:"K OVER 4.5", odds:110, tier:"T1", hit:false, actual:3, note:"3 Ks — LOSS", hit_prob:0.762},
      {player:"Chase Burns", prop:"K OVER 6.5", odds:-118, tier:"T1", hit:true, actual:8, note:"8 Ks — WIN", hit_prob:0.681},
      {player:"Cam Smith", prop:"H OVER 0.5", odds:-131, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.816},
      {player:"Ryan Kreidler", prop:"H OVER 0.5", odds:-105, tier:"T1", hit:"void", actual:0, note:"DNP / not in box scores — VOID", hit_prob:0.678},
      {player:"Brandon Valenzuela", prop:"H OVER 0.5", odds:-130, tier:"T1", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.666},
      {player:"Ketel Marte", prop:"TB OVER 1.5", odds:-105, tier:"T1", hit:true, actual:4, note:"4 TB — WIN", hit_prob:0.657},
    ],
    parlays: [],
  },
  {
    date: "2026-05-25",
    sport: "MLB",
    plays: [
      {player:"Trey Yesavage", prop:"K OVER 5.5", odds:-148, tier:"T1", hit:true, actual:6, note:"6 Ks — WIN", hit_prob:0.755},
      {player:"Michael Wacha", prop:"K OVER 4.5", odds:-150, tier:"T1", hit:true, actual:5, note:"5 Ks — WIN", hit_prob:0.726},
      {player:"Blake Dunn", prop:"H OVER 0.5", odds:-120, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.851},
      {player:"Alec Burleson", prop:"TB OVER 1.5", odds:140, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.461},
      {player:"Matt Chapman", prop:"H OVER 0.5", odds:-146, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.817},
      {player:"Gavin Sheets", prop:"H OVER 0.5", odds:-140, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.722},
      {player:"Alejandro Osuna", prop:"H OVER 0.5", odds:-147, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.696},
    ],
    parlays: [],
  },
  {
    date: "2026-05-24",
    sport: "MLB",
    plays: [
      {player:"Parker Messick", prop:"K OVER 5.5", odds:-152, tier:"AUTO", hit:true, actual:6, note:"6 Ks — WIN", hit_prob:0.925},
      {player:"Christian Scott", prop:"K OVER 4.5", odds:-130, tier:"AUTO", hit:true, actual:5, note:"5 Ks — WIN", hit_prob:0.8},
      {player:"Foster Griffin", prop:"K OVER 4.5", odds:105, tier:"T1", hit:true, actual:6, note:"6 Ks — WIN", hit_prob:0.723},
      {player:"Yoshinobu Yamamoto", prop:"K OVER 6.5", odds:-104, tier:"T1", hit:false, actual:3, note:"3 Ks — LOSS", hit_prob:0.686},
      {player:"Jake Bauers", prop:"H OVER 0.5", odds:-132, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.681},
      {player:"Carlos Narvaez", prop:"H OVER 0.5", odds:-118, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.665},
      {player:"Owen Caissie", prop:"H OVER 0.5", odds:-140, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.66},
    ],
    parlays: [],
  },
  {
    date: "2026-05-23",
    sport: "MLB",
    plays: [
      {player:"Paul Skenes", prop:"K OVER 6.5", odds:-122, tier:"AUTO", hit:false, actual:2, note:"2 Ks — LOSS", hit_prob:0.85},
      {player:"Taj Bradley", prop:"K OVER 4.5", odds:122, tier:"T1", hit:true, actual:7, note:"7 Ks — WIN", hit_prob:0.671},
      {player:"Jesus Sanchez", prop:"H OVER 0.5", odds:-110, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.876},
      {player:"Ryan Kreidler", prop:"H OVER 0.5", odds:-150, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.69},
      {player:"Carlos Narvaez", prop:"H OVER 0.5", odds:-140, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.665},
    ],
    parlays: [],
  },
  {
    date: "2026-05-22",
    sport: "MLB",
    plays: [
      {player:"Davis Martin", prop:"K OVER 4.5", odds:-153, tier:"AUTO", hit:true, actual:7, note:"7 Ks — WIN", hit_prob:0.926},
      {player:"Ezequiel Tovar", prop:"H OVER 0.5", odds:-148, tier:"T1", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.706},
      {player:"Richie Palacios", prop:"H OVER 0.5", odds:-145, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.684},
      {player:"Brandon Valenzuela", prop:"H OVER 0.5", odds:-125, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.801},
      {player:"Brett Baty", prop:"H OVER 0.5", odds:-140, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.71},
      {player:"Jesus Sanchez", prop:"H OVER 0.5", odds:-147, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.731},
      {player:"Josh Lowe", prop:"H OVER 0.5", odds:-115, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.697},
      {player:"Cristopher Sanchez", prop:"K OVER 6.5", odds:-120, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.746},
    ],
    parlays: [],
  },
  {
    date: "2026-05-21",
    sport: "MLB",
    plays: [
      {player:"Konnor Griffin", prop:"H OVER 0.5", odds:105, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.922},
      {player:"Daulton Varsho", prop:"H OVER 0.5", odds:-157, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.869},
      {player:"Keibert Ruiz", prop:"H OVER 0.5", odds:-177, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.857},
    ],
    parlays: [],
  },
  {
    date: "2026-05-20",
    sport: "MLB",
    plays: [
      {player:"Shohei Ohtani", prop:"TB OVER 1.5", odds:-115, tier:"T2", hit:false, actual:4, note:"4 TB — LOSS", hit_prob:0.647},
      {player:"Jake Bauers", prop:"H OVER 0.5", odds:-126, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.95},
      {player:"Cedric Mullins", prop:"H OVER 0.5", odds:-139, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.879},
      {player:"Nolan Gorman", prop:"H OVER 0.5", odds:-146, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.857},
      {player:"Kyle Isbel", prop:"H OVER 0.5", odds:-126, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.829},
      {player:"Jesus Sanchez", prop:"H OVER 0.5", odds:-133, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.709},
      {player:"Kyle Manzardo", prop:"H OVER 0.5", odds:-150, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.709},
    ],
    parlays: [],
  },
  {
    date: "2026-05-19",
    sport: "MLB",
    plays: [
      {player:"Nolan McLean", prop:"K OVER 5.5", odds:-150, tier:"AUTO", hit:false, actual:5, note:"5 Ks — LOSS", hit_prob:0.949},
      {player:"Landen Roupp", prop:"K OVER 4.5", odds:-138, tier:"AUTO", hit:false, actual:3, note:"3 Ks — LOSS", hit_prob:0.938},
      {player:"Will Warren", prop:"K OVER 5.5", odds:115, tier:"AUTO", hit:false, actual:3, note:"3 Ks — LOSS", hit_prob:0.905},
      {player:"Samuel Basallo", prop:"H OVER 0.5", odds:-135, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.944},
      {player:"Jake Bauers", prop:"H OVER 0.5", odds:-135, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.925},
      {player:"Taylor Walls", prop:"H OVER 0.5", odds:105, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.894},
      {player:"Michael Busch", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.86},
    ],
    parlays: [],
  },
  {
    date: "2026-05-18",
    sport: "MLB",
    plays: [
      {player:"Max Meyer", prop:"K OVER 4.5", odds:-125, tier:"AUTO", hit:true, actual:6, note:"6 Ks — WIN", hit_prob:0.95},
      {player:"Taylor Walls", prop:"H OVER 0.5", odds:-105, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.854},
      {player:"Teoscar Hernandez", prop:"H OVER 0.5", odds:-140, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.842},
      {player:"Gavin Sheets", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.817},
      {player:"Kody Clemens", prop:"H OVER 0.5", odds:-135, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.804},
      {player:"Travis Bazzana", prop:"H OVER 0.5", odds:-135, tier:"T1", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.734},
      {player:"Nick Fortes", prop:"H OVER 0.5", odds:-140, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.719},
    ],
    parlays: [],
  },
  {
    date: "2026-05-17",
    sport: "MLB",
    plays: [
      {player:"Paul Skenes", prop:"K OVER 6.5", odds:-142, tier:"T2", hit:true, actual:7, note:"7 Ks — WIN", hit_prob:0.563},
      {player:"Alejandro Osuna", prop:"H OVER 0.5", odds:-120, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.737},
      {player:"Aaron Judge", prop:"TB OVER 1.5", odds:105, tier:"T1", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.706},
      {player:"Luis Torrens", prop:"H OVER 0.5", odds:-140, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.681},
      {player:"Caleb Durbin", prop:"H OVER 0.5", odds:-145, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.653},
    ],
    parlays: [],
  },
  {
    date: "2026-05-16",
    sport: "MLB",
    plays: [
      {player:"Bryce Elder", prop:"K OVER 4.5", odds:-155, tier:"AUTO", hit:false, actual:3, note:"3 Ks — LOSS", hit_prob:0.893},
      {player:"Aaron Judge", prop:"TB OVER 1.5", odds:100, tier:"T1", hit:true, actual:3, note:"3 TB — WIN", hit_prob:0.706},
      {player:"Alejandro Osuna", prop:"H OVER 0.5", odds:-132, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.737},
      {player:"Tyrone Taylor", prop:"H OVER 0.5", odds:-145, tier:"T1", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.691},
      {player:"Caleb Durbin", prop:"H OVER 0.5", odds:-131, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.653},
    ],
    parlays: [],
  },
  {
    date: "2026-05-15",
    sport: "MLB",
    plays: [
      {player:"Spencer Strider", prop:"K OVER 6.5", odds:-105, tier:"SKIP", hit:false, actual:4, note:"4 Ks — LOSS", hit_prob:0.2},
      {player:"Kyle Freeland", prop:"H OVER 0.5", odds:118, tier:"", hit:false, actual:3, note:"3 hits — LOSS", hit_prob:null},
      {player:"Marcell Ozuna", prop:"H OVER 0.5", odds:-160, tier:"SKIP", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.468},
      {player:"Aaron Judge", prop:"TB OVER 1.5", odds:120, tier:"T1", hit:false, actual:1, note:"1 TB — LOSS", hit_prob:0.706},
      {player:"Mike Trout", prop:"H OVER 0.5", odds:-125, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.712},
      {player:"Colson Montgomery", prop:"H OVER 0.5", odds:-165, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.95},
      {player:"Bryan Reynolds", prop:"H OVER 0.5", odds:-190, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.848},
    ],
    parlays: [],
  },
  {
    date: "2026-05-14",
    sport: "MLB",
    plays: [
      {player:"Nolan McLean", prop:"K OVER 6.5", odds:115, tier:"SKIP", hit:true, actual:7, note:"7 Ks — WIN", hit_prob:0.542},
      {player:"Chris Sale", prop:"K OVER 6.5", odds:-152, tier:"T1", hit:true, actual:8, note:"8 Ks — WIN", hit_prob:0.723},
      {player:"Colson Montgomery", prop:"H OVER 0.5", odds:-150, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.95},
      {player:"Bo Bichette", prop:"H OVER 0.5", odds:-110, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.851},
      {player:"Xander Bogaerts", prop:"H OVER 0.5", odds:-148, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.931},
      {player:"Nico Hoerner", prop:"TB OVER 1.5", odds:128, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.433},
      {player:"Christian Walker", prop:"TB OVER 1.5", odds:130, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.417},
      {player:"Seiya Suzuki", prop:"H OVER 0.5", odds:-169, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.768},
      {player:"Mickey Moniak", prop:"H OVER 0.5", odds:155, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.713},
      {player:"Ryan Jeffers", prop:"H OVER 0.5", odds:-142, tier:"T2", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.644},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-160, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.928},
    ],
    parlays: [],
  },
  {
    date: "2026-05-13",
    sport: "MLB",
    plays: [
      {player:"Gunnar Henderson", prop:"H OVER 0.5", odds:180, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.737},
      {player:"Dylan Cease", prop:"K OVER 6.5", odds:104, tier:"SKIP", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.2},
      {player:"Mickey Moniak", prop:"TB OVER 1.5", odds:106, tier:"SKIP", hit:true, actual:3, note:"3 TB — WIN", hit_prob:0.2},
      {player:"Jacob Misiorowski", prop:"K OVER 7.5", odds:-144, tier:"SKIP", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.212},
      {player:"Colson Montgomery", prop:"H OVER 0.5", odds:-167, tier:"AUTO", hit:true, actual:3, note:"3 hits — WIN", hit_prob:0.95},
      {player:"Junior Caminero", prop:"TB OVER 1.5", odds:125, tier:"SKIP", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.421},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-174, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.928},
      {player:"Tyrone Taylor", prop:"H OVER 0.5", odds:-150, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.691},
      {player:"Xander Bogaerts", prop:"H OVER 0.5", odds:-164, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.931},
      {player:"Jonathan Aranda", prop:"H OVER 0.5", odds:-191, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.891},
      {player:"Ernie Clement", prop:"TB OVER 1.5", odds:150, tier:"SKIP", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.496},
    ],
    parlays: [],
  },
  {
    date: "2026-05-12",
    sport: "MLB",
    plays: [
      {player:"Colson Montgomery", prop:"TB OVER 1.5", odds:106, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.408},
      {player:"Aaron Judge", prop:"TB OVER 1.5", odds:-105, tier:"T1", hit:true, actual:2, note:"2 TB — WIN", hit_prob:0.712},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-242, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.928},
      {player:"Xander Bogaerts", prop:"H OVER 0.5", odds:-219, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.931},
      {player:"Jonathan Aranda", prop:"H OVER 0.5", odds:-192, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.891},
      {player:"Bryan Reynolds", prop:"TB OVER 1.5", odds:140, tier:"SKIP", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.2},
      {player:"Junior Caminero", prop:"TB OVER 1.5", odds:108, tier:"SKIP", hit:true, actual:2, note:"2 TB — WIN", hit_prob:0.421},
      {player:"Mickey Moniak", prop:"H OVER 0.5", odds:-140, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.713},
      {player:"Zack Wheeler", prop:"K OVER 6.5", odds:-125, tier:"T2", hit:false, actual:4, note:"4 Ks — LOSS", hit_prob:0.613},
      {player:"Ernie Clement", prop:"TB OVER 1.5", odds:155, tier:"SKIP", hit:true, actual:2, note:"2 TB — WIN", hit_prob:0.496},
      {player:"Bo Bichette", prop:"TB OVER 1.5", odds:120, tier:"SKIP", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.276},
      {player:"Lenyn Sosa", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.826},
      {player:"Pete Alonso", prop:"H OVER 0.5", odds:-184, tier:"T1", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.762},
      {player:"Matt Vierling", prop:"H OVER 0.5", odds:-150, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.731},
    ],
    parlays: [],
  },
  {
    date: "2026-05-11",
    sport: "MLB",
    plays: [
      {player:"Kevin Gausman", prop:"K OVER 4.5", odds:-158, tier:"T2", hit:true, actual:5, note:"5 Ks — WIN", hit_prob:0.559},
      {player:"Jonathan Aranda", prop:"TB OVER 1.5", odds:135, tier:"SKIP", hit:true, actual:2, note:"2 TB — WIN", hit_prob:0.2},
      {player:"Junior Caminero", prop:"TB OVER 1.5", odds:109, tier:"SKIP", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.421},
      {player:"Aaron Judge", prop:"TB OVER 1.5", odds:-110, tier:"T1", hit:true, actual:2, note:"2 TB — WIN", hit_prob:0.712},
      {player:"Lenyn Sosa", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:"void", actual:null, note:"DNP / not in box scores — VOID", hit_prob:0.826},
      {player:"Ernie Clement", prop:"H OVER 0.5", odds:-213, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.941},
      {player:"Pete Alonso", prop:"H OVER 0.5", odds:-155, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.762},
      {player:"Gunnar Henderson", prop:"H OVER 0.5", odds:-175, tier:"T1", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.737},
    ],
    parlays: [],
  },
  {
    date: "2026-05-10",
    sport: "MLB",
    plays: [
      {player:"Bryce Elder", prop:"K OVER 4.5", odds:-136, tier:"AUTO", hit:true, actual:8, note:"8 Ks — WIN", hit_prob:0.895},
      {player:"Noah Cameron", prop:"K OVER 4.5", odds:-144, tier:"AUTO", hit:false, actual:4, note:"4 Ks — LOSS", hit_prob:0.871},
      {player:"Logan Henderson", prop:"K OVER 5.5", odds:-156, tier:"T2", hit:false, actual:5, note:"5 Ks — LOSS", hit_prob:0.57},
      {player:"Ernie Clement", prop:"TB OVER 1.5", odds:145, tier:"SKIP", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.496},
      {player:"Nico Hoerner", prop:"TB OVER 1.5", odds:117, tier:"SKIP", hit:true, actual:2, note:"2 TB — WIN", hit_prob:0.436},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-195, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.928},
      {player:"Jonathan Aranda", prop:"TB OVER 1.5", odds:145, tier:"SKIP", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.2},
      {player:"Xander Bogaerts", prop:"TB OVER 1.5", odds:145, tier:"SKIP", hit:true, actual:2, note:"2 TB — WIN", hit_prob:0.2},
      {player:"Rafael Devers", prop:"H OVER 0.5", odds:-162, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.882},
      {player:"Aaron Judge", prop:"TB OVER 1.5", odds:105, tier:"T1", hit:true, actual:4, note:"4 TB — WIN", hit_prob:0.721},
      {player:"Colson Montgomery", prop:"H OVER 0.5", odds:-155, tier:"AUTO", hit:false, actual:0, note:"0 hits — LOSS", hit_prob:0.95},
      {player:"Brendan Donovan", prop:"TB OVER 1.5", odds:115, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.313},
    ],
    parlays: [],
  },
  {
    date: "2026-05-09",
    sport: "MLB",
    plays: [
      {player:"Colson Montgomery", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:true, actual:1, note:"1 hits — WIN", hit_prob:0.95},
      {player:"Ernie Clement", prop:"TB OVER 1.5", odds:140, tier:"SKIP", hit:true, actual:5, note:"5 TB — WIN", hit_prob:0.496},
      {player:"Miguel Vargas", prop:"H OVER 0.5", odds:-175, tier:"AUTO", hit:true, actual:2, note:"2 hits — WIN", hit_prob:0.928},
      {player:"Cam Schlittler", prop:"K OVER 5.5", odds:100, tier:"T2", hit:true, actual:6, note:"6 Ks — WIN", hit_prob:0.627},
      {player:"Joe Ryan", prop:"K OVER 4.5", odds:-142, tier:"T2", hit:true, actual:5, note:"5 Ks — WIN", hit_prob:0.556},
      {player:"Edward Cabrera", prop:"K OVER 5.5", odds:104, tier:"T2", hit:true, actual:6, note:"6 Ks — WIN", hit_prob:0.551},
      {player:"Ketel Marte", prop:"TB OVER 1.5", odds:-109, tier:"SKIP", hit:true, actual:1, note:"1 TB — WIN", hit_prob:0.2},
      {player:"Addison Barger", prop:"TB OVER 1.5", odds:135, tier:"AUTO", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.826},
      {player:"Nico Hoerner", prop:"TB OVER 1.5", odds:-103, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.436},
      {player:"Aaron Judge", prop:"TB OVER 1.5", odds:117, tier:"T1", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.721},
      {player:"Xander Bogaerts", prop:"TB OVER 1.5", odds:138, tier:"SKIP", hit:false, actual:0, note:"0 TB — LOSS", hit_prob:0.2},
    ],
    parlays: [],
  },
  {
    date: "2026-05-08",
    sport: "MLB",
    plays: [
      {player:"Kyle Bradish", prop:"K OVER 5.5", odds:-114, tier:"T1", hit:true, actual:10, note:"10 Ks — WIN", hit_prob:0.752},
      {player:"Connelly Early", prop:"K OVER 4.5", odds:105, tier:"T1", hit:true, actual:8, note:"8 Ks — WIN", hit_prob:0.683},
      {player:"Jacob Lopez", prop:"K OVER 4.5", odds:-135, tier:"T2", hit:true, actual:5, note:"5 Ks — WIN", hit_prob:0.599},
      {player:"Max Fried", prop:"K OVER 5.5", odds:-120, tier:"T2", hit:false, actual:5, note:"5 Ks — LOSS", hit_prob:0.603},
    ],
    parlays: [],
  },
];

const FADE_RESULTS = [
  {
    date: "2026-09-23",
    sport: "MLB",
    fades: [
      {player:"Isiah Kiner-Falefa", team:"", prop:"H UNDER 0.5", odds:126, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Maikel Garcia", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:3, note:"3 hit(s) — LOSS"},
      {player:"Austin Martin", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Ryan Jeffers", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-09-20",
    sport: "MLB",
    fades: [
      {player:"Angel Genao", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Maikel Garcia", team:"Arizona Diamondbacks", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Ke'Bryan Hayes", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Tommy Edman", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-09-18",
    sport: "MLB",
    fades: [
      {player:"Jac Caglianone", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Colson Montgomery", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Tommy Edman", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-09-17",
    sport: "MLB",
    fades: [
      {player:"Ke'Bryan Hayes", team:"", prop:"H UNDER 0.5", odds:125, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Brett Sullivan", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:2, note:"2 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-09-09",
    sport: "MLB",
    fades: [
      {player:"Jose Siri", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Taylor Ward", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-09-08",
    sport: "MLB",
    fades: [
      {player:"Jose Siri", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Konnor Griffin", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:2, note:"2 hit(s) — LOSS"},
      {player:"Taylor Ward", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Jake Cronenworth", team:"", prop:"H UNDER 0.5", odds:143, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
    ],
  },
  {
    date: "2026-09-02",
    sport: "MLB",
    fades: [
      {player:"Colt Keith", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Munetaka Murakami", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Taylor Ward", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Gary Sanchez", team:"Los Angeles Angels", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Griffin Conine", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-08-28",
    sport: "MLB",
    fades: [
      {player:"Cam Smith", team:"", prop:"H UNDER 0.5", odds:122, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
    ],
  },
  {
    date: "2026-08-27",
    sport: "MLB",
    fades: [
      {player:"Gary Sanchez", team:"", prop:"H UNDER 0.5", odds:115, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Nasim Nunez", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-08-26",
    sport: "MLB",
    fades: [
      {player:"Joc Pederson", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Jonah Heim", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:2, note:"2 hit(s) — LOSS"},
      {player:"Cooper Pratt", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:2, note:"2 hit(s) — LOSS"},
      {player:"Cam Smith", team:"Atlanta Braves", prop:"H UNDER 0.5", odds:115, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Brandon Nimmo", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-08-20",
    sport: "MLB",
    fades: [
      {player:"Heliot Ramos", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Isaac Collins", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-08-14",
    sport: "MLB",
    fades: [
      {player:"Hector Rodriguez", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"César Prieto", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-08-12",
    sport: "MLB",
    fades: [
      {player:"Esmerlyn Valdez", team:"Detroit Tigers", prop:"K UNDER 4.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Ben Rice", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-08-11",
    sport: "MLB",
    fades: [
      {player:"Carlos Cortes", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Ben Rice", team:"", prop:"H UNDER 0.5", odds:152, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
    ],
  },
  {
    date: "2026-08-10",
    sport: "MLB",
    fades: [
    ],
  },
  {
    date: "2026-08-06",
    sport: "MLB",
    fades: [
      {player:"Jorge Polanco", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Spencer Horwitz", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Leody Taveras", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Ke'Bryan Hayes", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-08-04",
    sport: "MLB",
    fades: [
      {player:"Carlos Cortes", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Leody Taveras", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Angel Martinez", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-07-30",
    sport: "MLB",
    fades: [
      {player:"Trent Grisham", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Nick Kurtz", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Ronald Acuna Jr.", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-07-28",
    sport: "MLB",
    fades: [
      {player:"Angel Martinez", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Cam Smith", team:"New York Mets", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Trent Grisham", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Tyler Callihan", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-07-25",
    sport: "MLB",
    fades: [
      {player:"Colton Cowser", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Kerry Carpenter", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Cam Smith", team:"Baltimore Orioles", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-07-21",
    sport: "MLB",
    fades: [
      {player:"Cam Smith", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Gavin Sheets", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Nathan Church", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Colby Thomas", team:"Kansas City Royals", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Ezequiel Tovar", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Corbin Carroll", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-07-19",
    sport: "MLB",
    fades: [
      {player:"Colby Thomas", team:"Kansas City Royals", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Kerry Carpenter", team:"", prop:"H UNDER 0.5", odds:140, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Nathan Church", team:"", prop:"H UNDER 0.5", odds:155, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Cedric Mullins", team:"", prop:"H UNDER 0.5", odds:129, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Henry Bolte", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Victor Robles", team:"", prop:"H UNDER 0.5", odds:120, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
    ],
  },
  {
    date: "2026-07-17",
    sport: "MLB",
    fades: [
      {player:"Troy Johnston", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Teoscar Hernandez", team:"Milwaukee Brewers", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Ryan Vilade", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Munetaka Murakami", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-07-12",
    sport: "MLB",
    fades: [
      {player:"Paul Goldschmidt", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Corbin Carroll", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-07-11",
    sport: "MLB",
    fades: [
      {player:"Leody Taveras", team:"", prop:"H UNDER 0.5", odds:128, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
    ],
  },
  {
    date: "2026-07-08",
    sport: "MLB",
    fades: [
      {player:"Dylan Beavers", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-07-07",
    sport: "MLB",
    fades: [
      {player:"Cody Bellinger", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-07-02",
    sport: "MLB",
    fades: [
      {player:"Ha-Seong Kim", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Drake Baldwin", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Hunter Feduccia", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Cooper Ingle", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-06-28",
    sport: "MLB",
    fades: [
      {player:"Drake Baldwin", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Jorge Mateo", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"Matt Chapman", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-06-26",
    sport: "MLB",
    fades: [
      {player:"Griffin Conine", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-06-24",
    sport: "MLB",
    fades: [
      {player:"Drake Baldwin", team:"", prop:"H UNDER 0.5", odds:150, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Randy Arozarena", team:"", prop:"H UNDER 0.5", odds:150, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Carlos Cortes", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Carlos Narvaez", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-06-23",
    sport: "MLB",
    fades: [
      {player:"Gabriel Rincones Jr.", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:2, note:"2 hit(s) — LOSS"},
      {player:"Drake Baldwin", team:"", prop:"H UNDER 0.5", odds:170, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Carlos Narvaez", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Spencer Steer", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
    ],
  },
  {
    date: "2026-06-20",
    sport: "MLB",
    fades: [
      {player:"Esmerlyn Valdez", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
      {player:"J.P. Crawford", team:"Philadelphia Phillies", prop:"H UNDER 0.5", odds:110, l14:"", hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-06-18",
    sport: "MLB",
    fades: [
    ],
  },
  {
    date: "2026-06-17",
    sport: "MLB",
    fades: [
    ],
  },
  {
    date: "2026-06-16",
    sport: "MLB",
    fades: [
      {player:"Ildemaro Vargas", team:"New York Yankees", prop:"H UNDER 0.5", odds:177, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Chandler Simpson", team:"", prop:"H UNDER 0.5", odds:154, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
    ],
  },
  {
    date: "2026-06-15",
    sport: "MLB",
    fades: [
      {player:"Joey Loperfido", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Jeff McNeil", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:3, note:"3 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-06-14",
    sport: "MLB",
    fades: [
      {player:"Chandler Simpson", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-06-13",
    sport: "MLB",
    fades: [
      {player:"J.T. Realmuto", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:3, note:"3 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-06-12",
    sport: "MLB",
    fades: [
      {player:"Chad Stevens", team:"", prop:"H UNDER 0.5", odds:127, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Denzer Guzman", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:2, note:"2 hit(s) — LOSS"},
      {player:"Jeff McNeil", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
    ],
  },
  {
    date: "2026-06-11",
    sport: "MLB",
    fades: [
    ],
  },
  {
    date: "2026-06-10",
    sport: "MLB",
    fades: [
      {player:"Jeff McNeil", team:"", prop:"H UNDER 0.5", odds:175, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Amed Rosario", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Anthony Volpe", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-06-09",
    sport: "MLB",
    fades: [
    ],
  },
  {
    date: "2026-06-08",
    sport: "MLB",
    fades: [
      {player:"Colby Thomas", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-06-07",
    sport: "MLB",
    fades: [
      {player:"Chad Stevens", team:"", prop:"H UNDER 0.5", odds:115, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Starling Marte", team:"Arizona Diamondbacks", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-06-06",
    sport: "MLB",
    fades: [
      {player:"Jorge Barrosa", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
    ],
  },
  {
    date: "2026-06-05",
    sport: "MLB",
    fades: [
      {player:"Edmundo Sosa", team:"", prop:"H UNDER 0.5", odds:150, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
    ],
  },
  {
    date: "2026-06-03",
    sport: "MLB",
    fades: [
      {player:"Matt McLain", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Ha-Seong Kim", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-06-01",
    sport: "MLB",
    fades: [
      {player:"Matt McLain", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Zach McKinstry", team:"Tampa Bay Rays", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Nolan Gorman", team:"", prop:"H UNDER 0.5", odds:75, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Jakob Marsee", team:"", prop:"H UNDER 0.5", odds:114, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Miguel Rojas", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-05-26",
    sport: "MLB",
    fades: [
      {player:"Adolis Garcia", team:"Pittsburgh Pirates", prop:"H UNDER 0.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Jackson Merrill", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Edouard Julien", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Kazuma Okamoto", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Caleb Durbin", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
    ],
  },
  {
    date: "2026-05-25",
    sport: "MLB",
    fades: [
      {player:"Moises Ballesteros", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:2, note:"2 hit(s) — LOSS"},
      {player:"Jackson Merrill", team:"San Francisco Giants", prop:"K UNDER 4.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Kazuma Okamoto", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-05-24",
    sport: "MLB",
    fades: [
      {player:"Cesar Prieto", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Edouard Julien", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Freddy Fermin", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Caleb Durbin", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Ryan McMahon", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-05-23",
    sport: "MLB",
    fades: [
      {player:"Edouard Julien", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Adolis Garcia", team:"Toronto Blue Jays", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"TJ Friedl", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Isaac Collins", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Jackson Merrill", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-05-22",
    sport: "MLB",
    fades: [
      {player:"Blake Perkins", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Caleb Durbin", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Colt Emerson", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Adolis Garcia", team:"Atlanta Braves", prop:"H UNDER 0.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Henry Davis", team:"San Francisco Giants", prop:"K UNDER 4.5", odds:110, l14:"", hit:false, actual:7, note:"7 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-05-21",
    sport: "MLB",
    fades: [
      {player:"MJ Melendez", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Henry Davis", team:"New York Yankees", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Austin Wells", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Jahmai Jones", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Zack Short", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Lenyn Sosa", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
    ],
  },
  {
    date: "2026-05-20",
    sport: "MLB",
    fades: [
      {player:"Victor Caratini", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:2, note:"2 hit(s) — LOSS"},
      {player:"Ozzie Albies", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:2, note:"2 hit(s) — LOSS"},
      {player:"Edouard Julien", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Ha-Seong Kim", team:"San Diego Padres", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
    ],
  },
  {
    date: "2026-05-19",
    sport: "MLB",
    fades: [
      {player:"Ha-Seong Kim", team:"Miami Marlins", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Manny Machado", team:"San Diego Padres", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Mitch Garver", team:"Seattle Mariners", prop:"H UNDER 0.5", odds:110, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Logan O'Hoppe", team:"Los Angeles Angels", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:2, note:"2 hit(s) — LOSS"},
      {player:"Nasim Nunez", team:"Washington Nationals", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:2, note:"2 hit(s) — LOSS"},
      {player:"Jacob Lopez", team:"Los Angeles Angels", prop:"K UNDER 5.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
    ],
  },
  {
    date: "2026-05-18",
    sport: "MLB",
    fades: [
      {player:"Ha-Seong Kim", team:"San Diego Padres", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Manny Machado", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"TJ Friedl", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Cam Smith", team:"Miami Marlins", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Nasim Nunez", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
    ],
  },
  {
    date: "2026-05-17",
    sport: "MLB",
    fades: [
      {player:"Corey Seager", team:"Houston Astros", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Ha-Seong Kim", team:"Atlanta Braves", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Manny Machado", team:"Seattle Mariners", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Matt Chapman", team:"Athletics", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Tyler O'Neill", team:"Washington Nationals", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Kevin Gausman", team:"Detroit Tigers", prop:"K UNDER 5.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
    ],
  },
  {
    date: "2026-05-16",
    sport: "MLB",
    fades: [
      {player:"Eduardo Rodriguez", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Sandy Alcantara", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Christian Walker", team:"Houston Astros", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Alec Bohm", team:"Pittsburgh Pirates", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:2, note:"2 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-05-15",
    sport: "MLB",
    fades: [
      {player:"Bo Bichette", team:"New York Mets", prop:"H UNDER 0.5", odds:200, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Alec Bohm", team:"Pittsburgh Pirates", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Aaron Nola", team:"Pittsburgh Pirates", prop:"K UNDER 5.5", odds:83, l14:"", hit:true, actual:2, note:"0 hits — WIN"},
      {player:"Sean Burke", team:"Chicago White Sox", prop:"K UNDER 4.5", odds:110, l14:"", hit:false, actual:5, note:"5 hit(s) — LOSS"},
      {player:"Manny Machado", team:"Seattle Mariners", prop:"H UNDER 0.5", odds:115, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Taylor Ward", team:"Washington Nationals", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-05-14",
    sport: "MLB",
    fades: [
      {player:"Manny Machado", team:"Milwaukee Brewers", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Caleb Durbin", team:"Boston Red Sox", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Royce Lewis", team:"Minnesota Twins", prop:"H UNDER 0.5", odds:106, l14:"", hit:true, actual:0, note:"0 hits — WIN"},
      {player:"Taylor Ward", team:"Minnesota Twins", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:1, note:"1 hit(s) — LOSS"},
      {player:"Alec Bohm", team:"Boston Red Sox", prop:"H UNDER 0.5", odds:110, l14:"", hit:false, actual:2, note:"2 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-05-13",
    sport: "MLB",
    fades: [
      {player:"Javier Sanoja", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Andres Gimenez", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Edouard Julien", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Moises Ballesteros", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Manny Machado", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Ramon Laureano", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Sonny Gray", team:"Boston Red Sox", prop:"K UNDER 4.5", odds:110, l14:"", hit:false, actual:6, note:"6 hit(s) — LOSS"},
    ],
  },
  {
    date: "2026-05-12",
    sport: "MLB",
    fades: [
      {player:"Manny Machado", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Taylor Ward", team:"Minnesota Twins", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Royce Lewis", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Josh Lowe", team:"Pittsburgh Pirates", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Coby Mayo", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Spencer Jones", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
    ],
  },
  {
    date: "2026-05-11",
    sport: "MLB",
    fades: [
      {player:"Taylor Ward", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Tyler O'Neill", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Rhys Hoskins", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Coby Mayo", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Andres Gimenez", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
      {player:"Richie Palacios", team:"", prop:"H UNDER 0.5", odds:110, l14:"", hit:"void", actual:null, note:"No result found — VOID"},
    ],
  },
  {
    date: "2026-05-10",
    sport: "MLB",
    fades: [
    ],
  },
  {
    date: "2026-05-09",
    sport: "MLB",
    fades: [
    ],
  },
  {
    date: "2026-05-08",
    sport: "MLB",
    fades: [
    ],
  },
];
// <<< AUTO-GENERATED DATA END

// ── RUN LINE RESULTS ──────────────────────────────────────────
const RL_RESULTS = [
  {
    date: "2026-05-26",
    rl: [
      {team:"Atlanta Braves",     bet:"ATL -1.5", odds:145, hit:null, actual:null, note:"Pending"},
      {team:"Tampa Bay Rays",     bet:"TB -1.5",  odds:140, hit:null, actual:null, note:"Pending"},
      {team:"Pittsburgh Pirates", bet:"PIT -1.5", odds:150, hit:null, actual:null, note:"Pending"},
    ],
  },
  {
    date: "2026-05-25",
    rl: [
      {team:"Los Angeles Dodgers", bet:"LAD -1.5", odds:100, hit:true,  actual:"W by 2", note:"LAD won by 2 — WIN +$100"},
      {team:"New York Yankees",    bet:"NYY -1.5", odds:null, hit:false, actual:"W by 1", note:"NYY won by 1 only — LOSS -$100"},
    ],
  },
  {
    date: "2026-05-24",
    rl: [
      {team:"Los Angeles Dodgers",   bet:"LAD -1.5", odds:133, hit:true,  actual:"W by 4", note:"LAD 11 @ MIL 3 — WIN +$133"},
      {team:"Arizona Diamondbacks",  bet:"ARI -1.5", odds:100, hit:true,  actual:"W by 1", note:"ARI 6 @ COL 4 — WIN +$100"},
      {team:"Pittsburgh Pirates",    bet:"PIT -1.5", odds:112, hit:false, actual:"L",      note:"PIT 2 @ TOR 5 — LOSS -$100"},
    ],
  },
  {
    date: "2026-05-23",
    rl: [
      {team:"Los Angeles Dodgers", bet:"LAD -1.5", odds:133, hit:true,  actual:"W by 8", note:"LAD 11 @ MIL 3 — WIN +$133"},
      {team:"Atlanta Braves",      bet:"ATL -1.5", odds:105, hit:false, actual:"L",      note:"WSH 2 @ ATL 0 — LOSS -$100"},
      {team:"Pittsburgh Pirates",  bet:"PIT -1.5", odds:112, hit:false, actual:"L",      note:"PIT 2 @ TOR 5 — LOSS -$100"},
    ],
  },
];

// ── MATH ──────────────────────────────────────────────────────
function calcPnl(plays, stake=100) {
  return plays.reduce((acc, p) => {
    // Skip pending and voided plays
    if (p.hit === null || p.hit === undefined || p.hit === "void") return acc;
    if (p.hit === true) {
      const odds = Number(p.odds);
      const ret  = odds < 0
        ? stake * (100 / Math.abs(odds))
        : stake * (odds / 100);
      return acc + ret;
    }
    // hit === false
    return acc - stake;
  }, 0);
}

function rlStats(date) {
  const day = RL_RESULTS.find(r => r.date === date);
  if (!day) return {hits:0, misses:0, total:0, pnl:0, rate:0};
  const settled = (day.rl||[]).filter(r => r.hit === true || r.hit === false);
  const hits    = settled.filter(r => r.hit === true).length;
  const misses  = settled.filter(r => r.hit === false).length;
  const pnl     = settled.reduce((acc, r) => {
    if (r.hit === true) {
      const o = Number(r.odds);
      return acc + (o < 0 ? 100*(100/Math.abs(o)) : 100*(o/100));
    }
    return acc - 100;
  }, 0);
  return {hits, misses, total:settled.length, pnl,
          rate: settled.length > 0 ? hits/settled.length : 0};
}

function allRlStats() {
  const all = RL_RESULTS.flatMap(d => (d.rl||[]).filter(r => r.hit === true || r.hit === false));
  const hits = all.filter(r => r.hit === true).length;
  const pnl  = all.reduce((acc, r) => {
    if (r.hit === true) {
      const o = Number(r.odds);
      return acc + (o < 0 ? 100*(100/Math.abs(o)) : 100*(o/100));
    }
    return acc - 100;
  }, 0);
  return {hits, total:all.length, pnl,
          rate: all.length > 0 ? hits/all.length : 0};
}


function fadeStats(day) {
  const fades   = day.fades || [];
  const settled = fades.filter(f => f.hit === true || f.hit === false);
  const hits    = settled.filter(f => f.hit === true).length;
  const misses  = settled.filter(f => f.hit === false).length;
  const pnl     = settled.reduce((acc, f) => {
    if (f.hit === true) {
      const o = Number(f.odds);
      return acc + (o < 0 ? 100*(100/Math.abs(o)) : 100*(o/100));
    }
    return acc - 100;
  }, 0);
  return {hits, misses, total:settled.length, pnl,
          rate: settled.length > 0 ? hits/settled.length : 0};
}

function allFadeStats(results) {
  const all     = results.flatMap(d => (d.fades||[]).filter(f => f.hit === true || f.hit === false));
  const hits    = all.filter(f => f.hit === true).length;
  const pnl     = all.reduce((acc, f) => {
    if (f.hit === true) {
      const o = Number(f.odds);
      return acc + (o < 0 ? 100*(100/Math.abs(o)) : 100*(o/100));
    }
    return acc - 100;
  }, 0);
  return {hits, total:all.length, pnl,
          rate: all.length > 0 ? hits/all.length : 0};
}

function dayStats(day) {
  const settled = day.plays.filter(p =>
    p.hit !== null && p.hit !== undefined && p.hit !== "void");
  const hits   = settled.filter(p => p.hit === true).length;
  const misses = settled.filter(p => p.hit === false).length;
  const voids  = day.plays.filter(p => p.hit === "void").length;
  const pnl    = calcPnl(day.plays);
  const rate   = settled.length > 0 ? hits / settled.length : 0;
  const pending= day.plays.filter(p =>
    p.hit === null || p.hit === undefined).length;

  const parlays    = day.parlays || [];
  const p_settled  = parlays.filter(p => p.hit !== null && p.hit !== "void");
  const p_hits     = p_settled.filter(p => p.hit === true).length;
  const p_pnl      = p_settled.reduce((a,p) =>
    a + (p.hit === true ? p.pnl : -100), 0);

  // Fade P&L — find matching date in FADE_RESULTS
  const fadeDay    = FADE_RESULTS.find(f => f.date === day.date);
  const fades      = fadeDay ? fadeDay.fades.filter(f => f.hit === true || f.hit === false) : [];
  const f_hits     = fades.filter(f => f.hit === true).length;
  const f_misses   = fades.filter(f => f.hit === false).length;
  const f_pnl      = fades.reduce((acc, f) => {
    if (f.hit === true) {
      const o = Number(f.odds);
      return acc + (o < 0 ? 100*(100/Math.abs(o)) : 100*(o/100));
    }
    return f.hit === false ? acc - 100 : acc;
  }, 0);
  const combined_pnl = pnl + f_pnl;  // parlays excluded — suspended

  // Run Line P&L
  const rl = rlStats(day.date);

  return {hits, misses, voids, total:settled.length, pnl, rate, pending,
          p_hits, p_total:p_settled.length, p_pnl,
          f_hits, f_misses, f_pnl,
          rl_hits:rl.hits, rl_misses:rl.misses, rl_pnl:rl.pnl, rl_total:rl.total};
}

function allStats(results, fadeResults) {
  const all    = results.flatMap(d =>
    d.plays.filter(p =>
      p.hit !== null && p.hit !== undefined && p.hit !== "void"));
  const hits   = all.filter(p => p.hit === true).length;
  const pnl    = calcPnl(all);
  const rate   = all.length > 0 ? hits / all.length : 0;

  // Fade totals
  const allFades  = (fadeResults||[]).flatMap(d =>
    (d.fades||[]).filter(f => f.hit === true || f.hit === false));
  const f_hits    = allFades.filter(f => f.hit === true).length;
  const f_misses  = allFades.filter(f => f.hit === false).length;
  const f_pnl     = allFades.reduce((acc, f) => {
    if (f.hit === true) {
      const o = Number(f.odds);
      return acc + (o < 0 ? 100*(100/Math.abs(o)) : 100*(o/100));
    }
    return f.hit === false ? acc - 100 : acc;
  }, 0);
  const f_rate    = allFades.length > 0 ? f_hits / allFades.length : 0;

  const byTier = {};
  all.forEach(p => {
    if (!byTier[p.tier]) byTier[p.tier] = {hits:0,total:0,pnl:0};
    byTier[p.tier].total++;
    if (p.hit === true) byTier[p.tier].hits++;
    byTier[p.tier].pnl += p.hit === true
      ? (p.odds < 0 ? 100*(100/Math.abs(p.odds)) : 100*(p.odds/100))
      : -100;
  });

  const bySport = {};
  results.forEach(d => {
    if (!bySport[d.sport]) bySport[d.sport] = {hits:0,total:0,pnl:0};
    d.plays.filter(p =>
      p.hit !== null && p.hit !== undefined && p.hit !== "void"
    ).forEach(p => {
      bySport[d.sport].total++;
      if (p.hit === true) bySport[d.sport].hits++;
      bySport[d.sport].pnl += p.hit === true
        ? (p.odds < 0 ? 100*(100/Math.abs(p.odds)) : 100*(p.odds/100))
        : -100;
    });
  });

  const allParlays = results.flatMap(d => d.parlays||[])
    .filter(p => p.hit !== null && p.hit !== "void");
  const p_hits = allParlays.filter(p => p.hit === true).length;
  const p_pnl  = allParlays.reduce((a,p) =>
    a + (p.hit === true ? p.pnl : -100), 0);

  return {hits, total:all.length, pnl, rate, byTier, bySport,
          p_hits, p_total:allParlays.length, p_pnl,
          f_hits, f_misses, f_pnl, f_rate};
}

// ── COMBINED SLATE STATS ─────────────────────────────────────
function combinedDayStats(day) {
  // Singles settled
  const singles  = day.plays.filter(p =>
    p.hit !== null && p.hit !== undefined && p.hit !== "void");
  const sHits    = singles.filter(p => p.hit === true).length;
  const sMisses  = singles.filter(p => p.hit === false).length;
  const sPnl     = singles.reduce((acc, p) => {
    if (p.hit === true) {
      const o = Number(p.odds);
      return acc + (o < 0 ? 100*(100/Math.abs(o)) : 100*(o/100));
    }
    return p.hit === false ? acc - 100 : acc;
  }, 0);

  // Fades settled — look up by date from FADE_RESULTS
  const fadeDay  = FADE_RESULTS.find(f => f.date === day.date);
  const fades    = fadeDay ? fadeDay.fades.filter(f => f.hit === true || f.hit === false) : [];
  const fHits    = fades.filter(f => f.hit === true).length;
  const fMisses  = fades.filter(f => f.hit === false).length;
  const fPnl     = fades.reduce((acc, f) => {
    if (f.hit === true) {
      const o = Number(f.odds);
      return acc + (o < 0 ? 100*(100/Math.abs(o)) : 100*(o/100));
    }
    return f.hit === false ? acc - 100 : acc;
  }, 0);

  // Parlays settled
  const parlays  = (day.parlays||[]).filter(p =>
    p.hit !== null && p.hit !== "void");
  const pHits    = parlays.filter(p => p.hit === true).length;
  const pMisses  = parlays.filter(p => p.hit === false).length;
  const pPnl     = parlays.reduce((a, p) =>
    a + (p.hit === true ? p.pnl : -100), 0);

  const totalHits   = sHits + fHits;
  const totalMisses = sMisses + fMisses;
  const totalPnl    = sPnl + fPnl + pPnl;
  const totalPlays  = singles.length + fades.length;

  return {
    sHits, sMisses, sPnl,
    fHits, fMisses, fPnl,
    pHits, pMisses, pPnl,
    totalHits, totalMisses, totalPnl,
    totalPlays,
    rate: totalPlays > 0 ? totalHits / totalPlays : 0,
  };
}

// ── STYLES ────────────────────────────────────────────────────
const T = {
  bg:"#060911", surface:"#0d1117", border:"#ffffff0a",
  accent:"#00ff88", text:"#f0f0f0", muted:"#555",
  mono:"'IBM Plex Mono',monospace", head:"'Barlow Condensed',sans-serif",
};

function StatBox({label, value, color, sub}) {
  return (
    <div style={{textAlign:"center",background:"#ffffff06",
      border:"1px solid #ffffff0a",borderRadius:8,
      padding:"12px 16px",minWidth:80}}>
      <div style={{fontSize:22,fontWeight:800,color:color||T.text,
        fontFamily:T.head}}>{value}</div>
      <div style={{fontSize:8,color:T.muted,letterSpacing:2,
        fontFamily:T.mono,marginTop:2}}>{label}</div>
      {sub && <div style={{fontSize:9,color:T.muted,
        fontFamily:T.mono,marginTop:2}}>{sub}</div>}
    </div>
  );
}

// ── DAY CARD ──────────────────────────────────────────────────
function DayCard({day, expanded, onToggle}) {
  const s = dayStats(day);
  const rateColor = s.total===0 ? "#555"
    : s.rate>=0.75 ? "#00ff88"
    : s.rate>=0.50 ? "#f5c518" : "#ff4757";
  const pnlColor = s.pnl >= 0 ? "#00ff88" : "#ff4757";
  const dateStr  = new Date(day.date+"T12:00:00")
    .toLocaleDateString("en-US",{weekday:"short",month:"short",day:"numeric"});
  const tierIcon = {AUTO:"⚡",T1:"★",T2:"◆",T3:"·"};

  return (
    <div onClick={onToggle} style={{background:T.surface,
      border:(expanded?"1px solid #ffffff18":"1px solid "+T.border),
      borderRadius:8,marginBottom:6,overflow:"hidden",
      cursor:"pointer",transition:"all 0.15s"}}>
      <div style={{padding:"12px 16px",display:"flex",
        alignItems:"center",gap:12}}>
        <div style={{minWidth:120}}>
          <div style={{fontSize:13,fontWeight:700,color:T.text,
            fontFamily:T.head}}>{dateStr}</div>
          <div style={{fontSize:9,color:T.muted,fontFamily:T.mono,
            letterSpacing:1,marginTop:2}}>{day.sport}</div>
        </div>
        <div style={{flex:1,display:"flex",gap:8,alignItems:"center"}}>
          {s.total > 0 ? (
            <>
              <div style={{fontSize:22,fontWeight:800,color:rateColor,
                fontFamily:T.head}}>{s.hits}-{s.misses}</div>
              <div style={{fontSize:11,color:T.muted,fontFamily:T.mono}}>
                ({(s.rate*100).toFixed(0)}%)
                {s.voids > 0 && " · " + s.voids + " void"}
              </div>
            </>
          ) : (
            <div style={{fontSize:13,color:T.muted,fontFamily:T.mono}}>
              {s.pending > 0 ? s.pending + " pending" : s.voids > 0 ? "PPD — all void" : "no results"}
            </div>
          )}
          {s.p_total > 0 && (
            <div style={{fontSize:10,color:"#f5c518",fontFamily:T.mono,
              background:"#f5c51815",border:"1px solid #f5c51830",
              padding:"2px 8px",borderRadius:4}}>
              🎯 {s.p_hits}-{s.p_total-s.p_hits} parlays
            </div>
          )}
          {s.f_hits + s.f_misses > 0 && (
            <div style={{fontSize:10,color:"#00e5ff",fontFamily:T.mono,
              background:"#00e5ff15",border:"1px solid #00e5ff30",
              padding:"2px 8px",borderRadius:4}}>
              📉 {s.f_hits}-{s.f_misses} fades {s.f_pnl>=0?"+":""}${s.f_pnl.toFixed(0)}
            </div>
          )}
        </div>
        <div style={{textAlign:"right"}}>
          {s.total > 0 && (
            <>
              <div style={{fontSize:16,fontWeight:700,color:pnlColor,
                fontFamily:T.mono}}>
                {s.pnl>=0?"+":""}${s.pnl.toFixed(0)}
              </div>
              <div style={{fontSize:8,color:T.muted,fontFamily:T.mono}}>
                singles @$100
              </div>
            </>
          )}
          {s.p_total > 0 && (
            <div style={{fontSize:11,fontWeight:700,
              color:s.p_pnl>=0?"#00ff88":"#ff4757",
              fontFamily:T.mono}}>
              {s.p_pnl>=0?"+":""}${s.p_pnl.toFixed(0)} parlays
            </div>
          )}
        </div>
        <div style={{fontSize:14,
          color:expanded?"#fff":"#333",
          transform:expanded?"rotate(180deg)":"none",
          transition:"transform 0.2s"}}>▾</div>
      </div>

      {expanded && (
        <div style={{borderTop:"1px solid "+T.border,padding:"12px 16px"}}>
          {/* Parlays section */}
          {day.parlays && day.parlays.length > 0 && (
            <div style={{marginBottom:12,padding:"10px 12px",
              background:"#f5c51810",border:"1px solid #f5c51830",
              borderRadius:6}}>
              <div style={{fontSize:9,color:"#f5c518",letterSpacing:2,
                fontFamily:T.mono,marginBottom:8}}>🎯 PARLAYS</div>
              {day.parlays.map((p,i) => (
                <div key={i} style={{display:"flex",
                  justifyContent:"space-between",alignItems:"flex-start",
                  fontSize:10,marginBottom:6,paddingBottom:6,
                  borderBottom:i<day.parlays.length-1
                    ?"1px solid #ffffff06":"none"}}>
                  <div>
                    <span style={{color:"#888",fontFamily:T.mono,
                      fontWeight:700}}>{p.id}: </span>
                    <span style={{color:"#666",fontFamily:T.mono}}>
                      {p.legs}
                    </span>
                    {p.note && (
                      <div style={{fontSize:9,color:"#444",
                        fontFamily:T.mono,marginTop:2}}>{p.note}</div>
                    )}
                  </div>
                  <div style={{display:"flex",gap:10,flexShrink:0,
                    marginLeft:12}}>
                    <span style={{color:"#666",fontFamily:T.mono}}>
                      {p.odds}
                    </span>
                    <span style={{fontWeight:700,fontFamily:T.mono,
                      color:p.hit==="void"?"#555"
                        :p.hit===true?"#00ff88":"#ff4757"}}>
                      {p.hit==="void" ? "— VOID"
                        :p.hit===true ? "✓ +$"+p.pnl
                        : "✗ -$100"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Singles */}
          {day.plays.map((p,i) => (
            <div key={i} style={{display:"flex",
              justifyContent:"space-between",alignItems:"center",
              padding:"7px 0",
              borderBottom:i<day.plays.length-1
                ?"1px solid "+T.border:"none"}}>
              <div style={{display:"flex",alignItems:"center",gap:8}}>
                <span style={{fontSize:9,fontWeight:700,
                  fontFamily:T.mono,
                  color:p.tier==="AUTO"?"#00ff88"
                    :p.tier==="T1"?"#f5c518":"#00e5ff"}}>
                  {tierIcon[p.tier]}{p.tier}
                </span>
                <span style={{fontSize:12,color:T.text,
                  fontWeight:600,fontFamily:T.head}}>{p.player}</span>
                <span style={{fontSize:10,color:T.muted,
                  fontFamily:T.mono}}>{p.prop}</span>
              </div>
              <div style={{display:"flex",gap:12,alignItems:"center"}}>
                <span style={{fontSize:10,color:"#888",fontFamily:T.mono}}>
                  {p.odds>0?"+":""}{p.odds}
                </span>
                {p.actual !== null && p.actual !== undefined && (
                  <span style={{fontSize:10,color:"#666",
                    fontFamily:T.mono}}>→ {p.actual}</span>
                )}
                <span style={{fontSize:11,fontWeight:700,fontFamily:T.mono,
                  color:p.hit===null?"#555"
                    :p.hit==="void"?"#888"
                    :p.hit===true?"#00ff88":"#ff4757"}}>
                  {p.hit===null?"PENDING"
                    :p.hit==="void"?"— VOID"
                    :p.hit===true?"✓ HIT":"✗ MISS"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── DAY CELL (module-level to avoid nested-function JSX parse issues) ────────
const DayCell = ({day, s, isToday}) => (
  <div style={{background: s && s.total>0
      ? s.rate>=0.75?"#00ff8818":s.rate>=0.50?"#f5c51818":"#ff475718"
      : "transparent",
    border:"1px solid "+(isToday?"#00e5ff":s&&s.total>0
      ?s.pnl>=0?"#00ff8840":"#ff475740"
      :T.border),
    borderRadius:5,padding:"4px 3px",minHeight:58,
    textAlign:"center"}}>
    <div style={{fontSize:9,
      color:isToday?"#00e5ff":T.muted,
      fontFamily:T.mono,
      fontWeight:isToday?700:400}}>{day}</div>
    {s && (s.total > 0 || s.voids > 0) && (
      <>
        <div style={{fontSize:11,fontWeight:800,
          color:s.total===0?"#555"
            :s.rate>=0.75?"#00ff88"
            :s.rate>=0.50?"#f5c518":"#ff4757",
          fontFamily:T.head,marginTop:1}}>
          {s.total===0?"PPD":s.hits+"-"+s.misses}
        </div>
        <div style={{fontSize:8,
          color:s.pnl>=0?"#00ff88":"#ff4757",
          fontFamily:T.mono}}>
          {s.pnl>=0?"+":""}${s.pnl.toFixed(0)}
        </div>
      </>
    )}
    {s && s.p_total > 0 && (
      <div style={{fontSize:8,
        color:s.p_pnl>=0?"#f5c518":"#ff6b35",
        fontFamily:T.mono,marginTop:1}}>
        🎯{s.p_hits}-{s.p_total-s.p_hits}
      </div>
    )}
    {s && s.pending > 0 && s.total === 0 && (
      <div style={{fontSize:8,color:"#555",
        fontFamily:T.mono,marginTop:4}}>{s.pending}p</div>
    )}
  </div>
);

// ── DUAL CALENDAR ─────────────────────────────────────────────
function CalendarView({results}) {
  const now     = new Date();
  const year    = now.getFullYear();
  const month   = now.getMonth();
  const first   = new Date(year,month,1).getDay();
  const daysInM = new Date(year,month+1,0).getDate();
  const monthNm = now.toLocaleDateString("en-US",
    {month:"long",year:"numeric"});

  const rMap = {};
  results.forEach(d => { rMap[d.date] = dayStats(d); });

  const todayStr = now.toISOString().split("T")[0];

  return (
    <div style={{background:T.surface,border:"1px solid "+T.border,
      borderRadius:8,padding:16,maxWidth:520}}>
      <div style={{fontSize:14,fontWeight:800,color:T.text,
        fontFamily:T.head,marginBottom:12}}>{monthNm}</div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(7,1fr)",
        gap:3,marginBottom:3}}>
        {["Su","Mo","Tu","We","Th","Fr","Sa"].map(d=>(
          <div key={d} style={{textAlign:"center",fontSize:9,
            color:T.muted,fontFamily:T.mono,padding:"3px 0"}}>{d}</div>
        ))}
      </div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(7,1fr)",gap:3}}>
        {Array(first).fill(null).map((_,i)=><div key={"e"+i}/>)}
        {Array(daysInM).fill(null).map((_,i)=>{
          const day = i+1;
          const ds = year+"-"+String(month+1).padStart(2,"0")+"-"+String(day).padStart(2,"0");
          return <DayCell key={day} day={day}
            s={rMap[ds]} isToday={ds===todayStr}/>;
        })}
      </div>
      <div style={{marginTop:10,display:"flex",gap:8,flexWrap:"wrap"}}>
        {[
          {color:"#00ff8818",border:"#00ff8840",label:"75%+ singles"},
          {color:"#f5c51818",border:"#f5c51840",label:"50-74%"},
          {color:"#ff475718",border:"#ff475740",label:"Under 50%"},
        ].map(l=>(
          <div key={l.label} style={{display:"flex",alignItems:"center",gap:5}}>
            <div style={{width:10,height:10,background:l.color,
              border:"1px solid "+l.border,borderRadius:2}}/>
            <span style={{fontSize:9,color:T.muted,fontFamily:T.mono}}>
              {l.label}
            </span>
          </div>
        ))}
        <div style={{display:"flex",alignItems:"center",gap:5}}>
          <span style={{fontSize:10}}>🎯</span>
          <span style={{fontSize:9,color:T.muted,fontFamily:T.mono}}>
            parlay W-L
          </span>
        </div>
      </div>
    </div>
  );
}

// ── MAIN ──────────────────────────────────────────────────────
export default function RecordTracker() {
  const [tab,      setTab]      = useState("slate");
  const [expanded, setExpanded] = useState(null);

  const stats        = allStats(RESULTS, FADE_RESULTS);
  const fadeStats_all = allFadeStats(FADE_RESULTS);
  const rlStats_all   = allRlStats();
  const TIER_ORD = ["AUTO","T1","T2","T3"];
  const TABS     = [
    {id:"slate",    label:"🎯 Full Slate"},
    {id:"overview", label:"📊 Overview"},
    {id:"calendar", label:"📅 Calendar"},
    {id:"parlays",  label:"🎯 Parlays"},
    {id:"log",      label:"📋 Day Log"},
    {id:"fades",    label:"📉 Fade Tracker"},
    {id:"runlines", label:"🏟️ Run Lines"},
  ];

  // All parlays across all days
  const allParlays = RESULTS.flatMap(d =>
    (d.parlays||[]).map(p => ({...p, date:d.date, sport:d.sport}))
  );

  // Slate totals (hoisted from JSX)
  const slateTotals = RESULTS.reduce((acc,day) => {
                const s = combinedDayStats(day);
                acc.wins += s.totalHits;
                acc.loss += s.totalMisses;
                acc.pnl  += s.totalPnl;
                return acc;
              }, {wins:0,loss:0,pnl:0});
              const slateTotalsRate = slateTotals.wins/(slateTotals.wins+slateTotals.loss||1);

  return (
    <div style={{background:T.bg,minHeight:"100vh",paddingBottom:60}}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500;700&display=swap');
        * { box-sizing:border-box; }
      `}</style>

      {/* Header */}
      <div style={{background:"#0a0f1a",
        borderBottom:"1px solid "+T.border,padding:"20px 24px 0"}}>
        <div style={{maxWidth:1280,margin:"0 auto"}}>
          <div style={{display:"flex",justifyContent:"space-between",
            alignItems:"flex-start",marginBottom:16,
            flexWrap:"wrap",gap:12}}>
            <div>
              <div style={{fontSize:11,color:T.muted,letterSpacing:3,
                fontFamily:T.mono,marginBottom:4}}>EDGE INDEX / RECORD</div>
              <div style={{fontSize:26,fontWeight:800,color:T.text,
                fontFamily:T.head,letterSpacing:1}}>
                PERFORMANCE TRACKER
              </div>
              <div style={{fontSize:11,color:T.muted,
                fontFamily:T.mono,marginTop:2}}>
                MLB · Singles + Fades · Daily P&L · No Parlays
              </div>
            </div>
            <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
              <StatBox label="SINGLES"
                value={stats.hits+"-"+(stats.total-stats.hits)}
                color={stats.rate>=0.65?"#00ff88":stats.rate>=0.50?"#f5c518":"#ff4757"}
                sub={(stats.rate*100).toFixed(0)+"%"}/>
              <StatBox label="SINGLES P&L"
                value={(stats.pnl>=0?"+":"")+"$"+stats.pnl.toFixed(0)}
                color={stats.pnl>=0?"#00ff88":"#ff4757"}
                sub={(stats.pnl>=0?"+":"")+(stats.pnl/100).toFixed(2)+"u"}/>
              <StatBox label="FADES"
                value={stats.f_hits+"-"+stats.f_misses}
                color={stats.f_rate>=0.60?"#00e5ff":stats.f_rate>=0.50?"#f5c518":"#888"}
                sub={(stats.f_rate*100).toFixed(0)+"%"}/>
              <StatBox label="FADES P&L"
                value={(stats.f_pnl>=0?"+":"")+"$"+stats.f_pnl.toFixed(0)}
                color={stats.f_pnl>=0?"#00ff88":"#ff4757"}
                sub={(stats.f_pnl>=0?"+":"")+(stats.f_pnl/100).toFixed(2)+"u"}/>
              <StatBox label="RUN LINES"
                value={rlStats_all.hits+"-"+(rlStats_all.total-rlStats_all.hits)}
                color={rlStats_all.rate>=0.60?"#f5c518":rlStats_all.rate>=0.50?"#888":"#ff4757"}
                sub={(rlStats_all.rate*100).toFixed(0)+"%"}/>
              <StatBox label="RL P&L"
                value={(rlStats_all.pnl>=0?"+":"")+"$"+rlStats_all.pnl.toFixed(0)}
                color={rlStats_all.pnl>=0?"#00ff88":"#ff4757"}
                sub={(rlStats_all.pnl>=0?"+":"")+(rlStats_all.pnl/100).toFixed(2)+"u"}/>
              <StatBox label="COMBINED"
                value={(stats.pnl+stats.f_pnl+rlStats_all.pnl>=0?"+":"")+"$"+(stats.pnl+stats.f_pnl+rlStats_all.pnl).toFixed(0)}
                color={(stats.pnl+stats.f_pnl+rlStats_all.pnl)>=0?"#00ff88":"#ff4757"}
                sub={(stats.pnl+stats.f_pnl+rlStats_all.pnl>=0?"+":"")+ ((stats.pnl+stats.f_pnl+rlStats_all.pnl)/100).toFixed(2)+"u"}/>
              <StatBox label="DAYS"
                value={RESULTS.length} color="#00e5ff"/>
            </div>
          </div>
          <div style={{display:"flex"}}>
            {TABS.map(t=>(
              <button key={t.id} onClick={()=>setTab(t.id)}
                style={{padding:"10px 18px",background:"transparent",
                  border:"none",
                  borderBottom:tab===t.id
                    ?"2px solid "+T.accent:"2px solid transparent",
                  color:tab===t.id?T.accent:T.muted,
                  fontSize:12,fontWeight:600,cursor:"pointer",
                  fontFamily:T.mono,transition:"all 0.15s"}}>
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{padding:"20px 24px",maxWidth:1280,margin:"0 auto"}}>

        {/* OVERVIEW */}
        {/* FULL SLATE */}
        {tab==="slate" && (
          <div>
            <div style={{marginBottom:16,padding:"12px 16px",
              background:"#ffffff06",border:"1px solid #ffffff0a",borderRadius:8}}>
              <div style={{fontSize:11,color:T.muted,fontFamily:T.mono,
                letterSpacing:1,marginBottom:4}}>COMBINED SLATE — ALL PLAYS</div>
              <div style={{fontSize:11,color:"#666",fontFamily:T.mono,lineHeight:1.6}}>
                Singles + Fades + Parlays combined per day.
                A bad overs day + good fades day = winning slate.
              </div>
            </div>

            {[...RESULTS].map((day,di) => {
              const s        = combinedDayStats(day);
              const dateStr  = new Date(day.date+"T12:00:00")
                .toLocaleDateString("en-US",{weekday:"short",month:"short",day:"numeric"});
              const pnlColor = s.totalPnl>=0?"#00ff88":"#ff4757";
              const rateColor= s.rate>=0.65?"#00ff88":s.rate>=0.50?"#f5c518":"#ff4757";
              return (
                <div key={di} style={{background:T.surface,
                  border:"1px solid "+T.border,borderRadius:8,marginBottom:8,padding:16}}>
                  <div style={{display:"flex",justifyContent:"space-between",
                    alignItems:"center",marginBottom:12}}>
                    <div>
                      <div style={{fontSize:16,fontWeight:800,color:T.text,
                        fontFamily:T.head}}>{dateStr}</div>
                      <div style={{fontSize:9,color:T.muted,fontFamily:T.mono,marginTop:2}}>
                        {day.sport}
                      </div>
                    </div>
                    <div style={{textAlign:"right"}}>
                      <div style={{fontSize:22,fontWeight:800,color:pnlColor,fontFamily:T.head}}>
                        {s.totalPnl>=0?"+":""}${s.totalPnl.toFixed(0)}
                      </div>
                      <div style={{fontSize:9,color:T.muted,fontFamily:T.mono}}>combined P&L</div>
                    </div>
                  </div>
                  <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:8}}>
                    <div style={{background:"#ffffff06",borderRadius:6,padding:"10px 12px",
                      borderLeft:"3px solid "+(s.sPnl>=0?"#00ff88":"#ff4757")}}>
                      <div style={{fontSize:9,color:T.muted,fontFamily:T.mono,
                        letterSpacing:1,marginBottom:6}}>⚾ SINGLES</div>
                      <div style={{fontSize:18,fontWeight:800,
                        color:s.sHits/(s.sHits+s.sMisses||1)>=0.65?"#00ff88":"#f5c518",
                        fontFamily:T.head}}>{s.sHits}-{s.sMisses}</div>
                      <div style={{fontSize:11,color:s.sPnl>=0?"#00ff88":"#ff4757",
                        fontFamily:T.mono,marginTop:4}}>
                        {s.sPnl>=0?"+":""}${s.sPnl.toFixed(0)}
                      </div>
                    </div>
                    <div style={{background:"#ffffff06",borderRadius:6,padding:"10px 12px",
                      borderLeft:"3px solid "+(s.fPnl>=0?"#00e5ff":"#555")}}>
                      <div style={{fontSize:9,color:"#00e5ff",fontFamily:T.mono,
                        letterSpacing:1,marginBottom:6}}>📉 FADES</div>
                      {s.fHits+s.fMisses > 0 ? (
                        <>
                          <div style={{fontSize:18,fontWeight:800,
                            color:s.fHits/(s.fHits+s.fMisses)>=0.60?"#00e5ff":"#f5c518",
                            fontFamily:T.head}}>{s.fHits}-{s.fMisses}</div>
                          <div style={{fontSize:11,color:s.fPnl>=0?"#00ff88":"#ff4757",
                            fontFamily:T.mono,marginTop:4}}>
                            {s.fPnl>=0?"+":""}${s.fPnl.toFixed(0)}
                          </div>
                        </>
                      ) : (
                        <div style={{fontSize:11,color:"#555",fontFamily:T.mono}}>no fades</div>
                      )}
                    </div>
                    <div style={{background:"#ffffff06",borderRadius:6,padding:"10px 12px",
                      borderLeft:"3px solid "+(s.pPnl>=0?"#f5c518":"#888")}}>
                      <div style={{fontSize:9,color:T.muted,fontFamily:T.mono,
                        letterSpacing:1,marginBottom:6}}>🎯 PARLAYS</div>
                      {s.pHits+s.pMisses > 0 ? (
                        <>
                          <div style={{fontSize:18,fontWeight:800,color:"#f5c518",
                            fontFamily:T.head}}>{s.pHits}-{s.pMisses}</div>
                          <div style={{fontSize:11,color:s.pPnl>=0?"#00ff88":"#ff4757",
                            fontFamily:T.mono,marginTop:4}}>
                            {s.pPnl>=0?"+":""}${s.pPnl.toFixed(0)}
                          </div>
                        </>
                      ) : (
                        <div style={{fontSize:11,color:"#555",fontFamily:T.mono}}>no parlays</div>
                      )}
                    </div>
                  </div>
                  <div style={{marginTop:10,padding:"8px 12px",
                    background:s.totalPnl>=0?"#00ff8808":"#ff475708",
                    borderRadius:6,display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                    <div style={{fontSize:11,color:rateColor,fontFamily:T.mono,fontWeight:700}}>
                      {s.totalHits}-{s.totalMisses} combined ({(s.rate*100).toFixed(0)}%)
                    </div>
                    <div style={{display:"flex",gap:16}}>
                      <div style={{textAlign:"center"}}>
                        <div style={{fontSize:14,fontWeight:800,color:pnlColor,fontFamily:T.head}}>
                          {s.totalPnl>=0?"+":""}${s.totalPnl.toFixed(0)}
                        </div>
                        <div style={{fontSize:8,color:T.muted,fontFamily:T.mono}}>P&L</div>
                      </div>
                      <div style={{textAlign:"center"}}>
                        <div style={{fontSize:14,fontWeight:800,color:pnlColor,fontFamily:T.head}}>
                          {s.totalPnl>=0?"+":""}{(s.totalPnl/100).toFixed(2)}u
                        </div>
                        <div style={{fontSize:8,color:T.muted,fontFamily:T.mono}}>UNITS</div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}

            <div style={{marginTop:8,padding:"14px 16px",
                  background:slateTotals.pnl>=0?"#00ff8810":"#ff475710",
                  border:"1px solid "+(slateTotals.pnl>=0?"#00ff8830":"#ff475730"),
                  borderRadius:8}}>
                  <div style={{fontSize:14,fontWeight:800,
                    color:slateTotals.pnl>=0?"#00ff88":"#ff4757",fontFamily:T.head}}>
                    ALL-TIME: {slateTotals.wins}-{slateTotals.loss} ({(slateTotalsRate*100).toFixed(1)}%)
                    {" · "}{slateTotals.pnl>=0?"+":""}${slateTotals.pnl.toFixed(0)}
                    {" · "}{slateTotals.pnl>=0?"+":""}{(slateTotals.pnl/100).toFixed(2)}u
                  </div>
                  <div style={{fontSize:10,color:T.muted,fontFamily:T.mono,marginTop:4}}>
                    Singles + Fades combined {"·"} Parlays shown separately
                  </div>
                </div>
          </div>
        )}

        {/* FADE TRACKER */}
        {tab==="fades" && (
          <div>
            <div style={{display:"flex",gap:12,marginBottom:16,flexWrap:"wrap"}}>
              {[
                {label:"FADE RECORD",
                 val:fadeStats_all.hits+"-"+(fadeStats_all.total-fadeStats_all.hits),
                 color:"#00e5ff"},
                {label:"HIT RATE",
                 val:fadeStats_all.total>0?(fadeStats_all.rate*100).toFixed(0)+"%":"-",
                 color:fadeStats_all.rate>=0.60?"#00e5ff":"#888"},
                {label:"P&L @$100",
                 val:(fadeStats_all.pnl>=0?"+":"")+"$"+fadeStats_all.pnl.toFixed(0),
                 color:fadeStats_all.pnl>=0?"#00ff88":"#ff4757"},
              ].map(s=>(
                <div key={s.label} style={{textAlign:"center",
                  background:"#ffffff06",border:"1px solid #ffffff0a",
                  borderRadius:8,padding:"12px 20px",minWidth:100}}>
                  <div style={{fontSize:22,fontWeight:800,color:s.color,fontFamily:T.head}}>
                    {s.val}
                  </div>
                  <div style={{fontSize:8,color:T.muted,letterSpacing:2,
                    fontFamily:T.mono,marginTop:2}}>{s.label}</div>
                </div>
              ))}
            </div>
            <div style={{marginBottom:12,padding:"10px 14px",
              background:"#00e5ff10",border:"1px solid #00e5ff30",borderRadius:8}}>
              <div style={{fontSize:10,color:"#00e5ff",fontFamily:T.mono,lineHeight:1.6}}>
                <strong>Fade logic:</strong> Players with L14 avg below .150 faded on UNDER.
                Plus money UNDERs (+100 to +175) offer best value. Extreme cold bats
                (.000-.080) have highest confidence. K UNDERs: 0.75 K/IP or below.
              </div>
            </div>
            {FADE_RESULTS.map((day,di) => {
              const s = fadeStats(day);
              const dateStr = new Date(day.date+"T12:00:00")
                .toLocaleDateString("en-US",{weekday:"short",month:"short",day:"numeric"});
              return (
                <div key={di} style={{background:T.surface,
                  border:"1px solid "+T.border,borderRadius:8,marginBottom:8,overflow:"hidden"}}>
                  <div style={{padding:"10px 16px",display:"flex",
                    justifyContent:"space-between",alignItems:"center",
                    borderBottom:"1px solid "+T.border}}>
                    <div style={{fontSize:13,fontWeight:700,color:T.text,fontFamily:T.head}}>
                      {dateStr}
                    </div>
                    <div style={{display:"flex",gap:16,alignItems:"center"}}>
                      <span style={{fontSize:13,fontWeight:800,
                        color:s.rate>=0.60?"#00e5ff":"#888",fontFamily:T.head}}>
                        {s.hits}-{s.misses}
                      </span>
                      <span style={{fontSize:11,
                        color:s.pnl>=0?"#00ff88":"#ff4757",fontFamily:T.mono}}>
                        {s.pnl>=0?"+":""}${s.pnl.toFixed(0)}
                      </span>
                    </div>
                  </div>
                  {/* Column headers */}
                  <div style={{display:"grid",
                    gridTemplateColumns:"1fr 80px 90px 100px 110px",
                    gap:8,padding:"6px 16px",
                    borderBottom:"1px solid "+T.border,
                    background:"#ffffff04"}}>
                    {["PLAYER","SIGNAL","PLAY","UNDER ODDS","RESULT"].map(h=>(
                      <div key={h} style={{fontSize:8,color:T.muted,
                        fontFamily:T.mono,letterSpacing:2}}>{h}</div>
                    ))}
                  </div>
                  {day.fades.map((f,i) => {
                    const underPlay = f.prop.includes("K") ? "K UNDER "+f.prop.split(" ").pop() : "H UNDER 0.5";
                    const underOdds = f.odds > 0 ? "+"+f.odds : String(f.odds);
                    return (
                      <div key={i} style={{display:"grid",
                        gridTemplateColumns:"1fr 80px 90px 100px 110px",
                        gap:8,alignItems:"center",padding:"9px 16px",
                        borderBottom:i<day.fades.length-1?"1px solid "+T.border:"none",
                        background:i%2===0?"transparent":"#ffffff02"}}>
                        <div style={{display:"flex",gap:8,alignItems:"center"}}>
                          <span style={{fontSize:9,color:"#00e5ff",fontFamily:T.mono,
                            fontWeight:700,background:"#00e5ff15",padding:"2px 6px",
                            borderRadius:3}}>FADE</span>
                          <span style={{fontSize:13,color:T.text,fontWeight:600,
                            fontFamily:T.head}}>{f.player}</span>
                          <span style={{fontSize:9,color:T.muted,fontFamily:T.mono}}>{f.team}</span>
                        </div>
                        <div style={{fontSize:10,color:"#f5c518",fontFamily:T.mono}}>
                          {f.l14} L14
                        </div>
                        <div style={{fontSize:10,color:"#00e5ff",fontFamily:T.mono,fontWeight:700}}>
                          {underPlay}
                        </div>
                        <div style={{fontSize:11,color:"#00ff88",fontFamily:T.mono,fontWeight:700}}>
                          {underOdds}
                        </div>
                        <div style={{fontSize:11,fontWeight:700,fontFamily:T.mono,
                          color:f.hit===true?"#00ff88":f.hit===false?"#ff4757":"#555"}}>
                          {f.hit===true?"✓ HIT ("+underOdds+")":f.hit===false?"✗ MISS":"PENDING"}
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })}
            <div style={{marginTop:12,padding:"10px 14px",background:"#ffffff06",
              borderRadius:8,border:"1px solid #ffffff0a"}}>
              <div style={{fontSize:10,color:T.muted,fontFamily:T.mono,lineHeight:1.6}}>
                <strong style={{color:"#f5c518"}}>Threshold notes:</strong>
                {" "}Below .100 L14 = strongest signal. .100-.150 = moderate.
                Plus money (+100 to +175) maximizes value. Avoid fading players
                returning from injury — breakout risk.
              </div>
            </div>
          </div>
        )}

        {tab==="overview" && (
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
            {/* By Tier */}
            <div style={{background:T.surface,
              border:"1px solid "+T.border,borderRadius:8,padding:16}}>
              <div style={{fontSize:13,fontWeight:800,color:T.text,
                fontFamily:T.head,letterSpacing:1,marginBottom:12}}>
                SINGLES BY TIER
              </div>
              {TIER_ORD.filter(t=>stats.byTier[t]).map(tier=>{
                const s = stats.byTier[tier];
                const rate = s.total>0?s.hits/s.total:0;
                const color = tier==="AUTO"?"#00ff88"
                  :tier==="T1"?"#f5c518"
                  :tier==="T2"?"#00e5ff":"#888";
                return (
                  <div key={tier} style={{display:"flex",
                    justifyContent:"space-between",alignItems:"center",
                    padding:"8px 0",borderBottom:"1px solid "+T.border}}>
                    <div style={{display:"flex",alignItems:"center",gap:8}}>
                      <span style={{fontSize:10,color,fontWeight:700,
                        fontFamily:T.mono,minWidth:45}}>{tier}</span>
                      <span style={{fontSize:13,color:T.text,
                        fontFamily:T.head,fontWeight:700}}>
                        {s.hits}-{s.total-s.hits}
                      </span>
                    </div>
                    <div style={{display:"flex",gap:16}}>
                      <span style={{fontSize:11,color,fontFamily:T.mono}}>
                        {(rate*100).toFixed(0)}%
                      </span>
                      <span style={{fontSize:11,fontFamily:T.mono,
                        color:s.pnl>=0?"#00ff88":"#ff4757"}}>
                        {s.pnl>=0?"+":""}${s.pnl.toFixed(0)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* By Sport */}
            <div style={{background:T.surface,
              border:"1px solid "+T.border,borderRadius:8,padding:16}}>
              <div style={{fontSize:13,fontWeight:800,color:T.text,
                fontFamily:T.head,letterSpacing:1,marginBottom:12}}>
                BY SPORT
              </div>
              {Object.entries(stats.bySport).map(([sport,s])=>{
                const rate = s.total>0?s.hits/s.total:0;
                const color = sport==="NFL"?"#00e5ff":"#f5c518";
                return (
                  <div key={sport} style={{display:"flex",
                    justifyContent:"space-between",alignItems:"center",
                    padding:"8px 0",borderBottom:"1px solid "+T.border}}>
                    <div style={{display:"flex",alignItems:"center",gap:8}}>
                      <span style={{fontSize:13,color,fontWeight:700,
                        fontFamily:T.head,minWidth:50}}>{sport}</span>
                      <span style={{fontSize:13,color:T.text,
                        fontFamily:T.head,fontWeight:700}}>
                        {s.hits}-{s.total-s.hits}
                      </span>
                    </div>
                    <div style={{display:"flex",gap:16}}>
                      <span style={{fontSize:11,color,fontFamily:T.mono}}>
                        {(rate*100).toFixed(0)}%
                      </span>
                      <span style={{fontSize:11,fontFamily:T.mono,
                        color:s.pnl>=0?"#00ff88":"#ff4757"}}>
                        {s.pnl>=0?"+":""}${s.pnl.toFixed(0)}
                      </span>
                    </div>
                  </div>
                );
              })}
              <div style={{marginTop:10,padding:"8px 10px",
                background:"#ffffff06",borderRadius:6}}>
                <div style={{fontSize:9,color:T.muted,fontFamily:T.mono,
                  letterSpacing:1}}>BREAK-EVEN REFERENCE</div>
                <div style={{fontSize:10,color:"#666",fontFamily:T.mono,
                  marginTop:4,lineHeight:1.6}}>
                  -110: 52.4% · -130: 56.5% · -150: 60.0%
                </div>
              </div>
            </div>

            {/* Recent form */}
            <div style={{gridColumn:"1/-1",background:T.surface,
              border:"1px solid "+T.border,borderRadius:8,padding:16}}>
              <div style={{fontSize:13,fontWeight:800,color:T.text,
                fontFamily:T.head,letterSpacing:1,marginBottom:12}}>
                RECENT FORM
              </div>
              <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
                {[...RESULTS].slice(0,14).map((d,i)=>{
                  const s = dayStats(d);
                  const color = s.total===0?"#555"
                    :s.rate>=0.75?"#00ff88"
                    :s.rate>=0.50?"#f5c518":"#ff4757";
                  const label = new Date(d.date+"T12:00:00")
                    .toLocaleDateString("en-US",
                      {month:"numeric",day:"numeric"});
                  return (
                    <div key={i} style={{textAlign:"center",
                      background:color+"18",
                      border:"1px solid "+color+"40",
                      borderRadius:6,padding:"8px 10px",minWidth:72}}>
                      <div style={{fontSize:9,color:T.muted,
                        fontFamily:T.mono,marginBottom:4}}>{label}</div>
                      {s.total > 0 ? (
                        <>
                          <div style={{fontSize:15,fontWeight:800,
                            color,fontFamily:T.head}}>
                            {s.hits}-{s.misses}
                          </div>
                          <div style={{fontSize:9,
                            color:s.pnl>=0?"#00ff88":"#ff4757",
                            fontFamily:T.mono}}>
                            {s.pnl>=0?"+":""}${s.pnl.toFixed(0)}
                          </div>
                          {s.p_total>0 && (
                            <div style={{fontSize:9,
                              color:s.p_pnl>=0?"#f5c518":"#ff6b35",
                              fontFamily:T.mono}}>
                              🎯{s.p_hits}-{s.p_total-s.p_hits}
                            </div>
                          )}
                        </>
                      ) : (
                        <div style={{fontSize:11,color:"#555",
                          fontFamily:T.mono}}>
                          {s.pending}p
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* CALENDAR */}
        {tab==="calendar" && <CalendarView results={RESULTS}/>}

        {/* PARLAYS TAB */}
        {tab==="parlays" && (
          <div>
            {/* Parlay summary */}
            <div style={{display:"flex",gap:12,marginBottom:16,
              flexWrap:"wrap"}}>
              {[
                {label:"PARLAY RECORD",
                 val:stats.p_hits+"-"+(stats.p_total-stats.p_hits),
                 color:"#f5c518"},
                {label:"HIT RATE",
                 val:(stats.p_total>0?((stats.p_hits/stats.p_total)*100).toFixed(0):"-")+"%",
                 color:"#f5c518"},
                {label:"P&L @$100",
                 val:(stats.p_pnl>=0?"+":"")+"$"+stats.p_pnl.toFixed(0),
                 color:stats.p_pnl>=0?"#00ff88":"#ff4757"},
                {label:"AVG ODDS",
                 val: allParlays.filter(p=>p.hit!==null).length > 0
                   ? allParlays.filter(p=>p.odds).slice(-1)[0]?.odds||"-"
                   : "-",
                 color:"#888"},
              ].map(s=>(
                <div key={s.label} style={{textAlign:"center",
                  background:"#ffffff06",border:"1px solid #ffffff0a",
                  borderRadius:8,padding:"12px 20px",minWidth:100}}>
                  <div style={{fontSize:22,fontWeight:800,color:s.color,
                    fontFamily:T.head}}>{s.val}</div>
                  <div style={{fontSize:8,color:T.muted,letterSpacing:2,
                    fontFamily:T.mono,marginTop:2}}>{s.label}</div>
                </div>
              ))}
            </div>

            {/* Parlay history */}
            <div style={{background:T.surface,
              border:"1px solid "+T.border,borderRadius:8,
              overflow:"hidden"}}>
              <div style={{display:"grid",
                gridTemplateColumns:"60px 80px 1fr 80px 80px 90px",
                gap:8,padding:"8px 16px",
                borderBottom:"1px solid "+T.border}}>
                {["DATE","ID","LEGS","ODDS","HIT PROB","RESULT"].map(h=>(
                  <div key={h} style={{fontSize:8,color:T.muted,
                    fontFamily:T.mono,letterSpacing:2}}>{h}</div>
                ))}
              </div>
              {allParlays.length === 0 && (
                <div style={{padding:24,textAlign:"center",
                  color:T.muted,fontFamily:T.mono,fontSize:11}}>
                  No parlays logged yet
                </div>
              )}
              {[...allParlays].map((p,i)=>(
                <div key={i} style={{display:"grid",
                  gridTemplateColumns:"60px 80px 1fr 80px 80px 90px",
                  gap:8,padding:"10px 16px",
                  borderBottom:"1px solid "+T.border,
                  background:i%2===0?"transparent":"#ffffff03"}}>
                  <div style={{fontSize:10,color:T.muted,
                    fontFamily:T.mono}}>{p.date.slice(5)}</div>
                  <div style={{fontSize:10,color:"#888",
                    fontFamily:T.mono,fontWeight:700}}>{p.id}</div>
                  <div style={{fontSize:10,color:"#666",
                    fontFamily:T.mono,overflow:"hidden",
                    textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                    {p.legs}
                  </div>
                  <div style={{fontSize:11,color:"#00ff88",
                    fontFamily:T.mono,fontWeight:700}}>{p.odds}</div>
                  <div style={{fontSize:10,color:T.muted,
                    fontFamily:T.mono}}>
                    {p.hit_prob ? (p.hit_prob*100).toFixed(0)+"%" : "—"}
                  </div>
                  <div style={{fontSize:11,fontWeight:700,
                    fontFamily:T.mono,
                    color:p.hit===true?"#00ff88"
                      :p.hit===false?"#ff4757":"#555"}}>
                    {p.hit===true?"✓ +$"+p.pnl
                      :p.hit===false?"✗ -$100"
                      :p.hit==="void"?"— VOID":"PENDING"}
                  </div>
                </div>
              ))}
            </div>

            {allParlays.length > 0 && (
              <div style={{marginTop:12,padding:"10px 16px",
                background:stats.p_pnl>=0?"#00ff8810":"#ff475710",
                border:"1px solid "+(stats.p_pnl>=0?"#00ff8830":"#ff475730"),
                borderRadius:8}}>
                <div style={{fontSize:13,fontWeight:800,
                  color:stats.p_pnl>=0?"#00ff88":"#ff4757",
                  fontFamily:T.head}}>
                  {stats.p_hits}-{stats.p_total-stats.p_hits} PARLAYS ·{" "}
                  {stats.p_total>0?((stats.p_hits/stats.p_total)*100).toFixed(0):0}% HIT RATE ·{" "}
                  {stats.p_pnl>=0?"+":""}${stats.p_pnl.toFixed(0)} P&L
                </div>
                <div style={{fontSize:10,color:T.muted,
                  fontFamily:T.mono,marginTop:4}}>
                  Flat $100/parlay · Combined: {(stats.pnl+stats.p_pnl)>=0?"+":""}
                  ${(stats.pnl+stats.p_pnl).toFixed(0)} ·{" "}
                  {(stats.pnl+stats.p_pnl)>=0?"+":""}
                  {((stats.pnl+stats.p_pnl)/100).toFixed(2)}u total
                </div>
              </div>
            )}
          </div>
        )}

        {/* DAY LOG */}
        {tab==="log" && (
          <>
            <div style={{marginBottom:12,fontSize:11,
              color:T.muted,fontFamily:T.mono}}>
              {RESULTS.length} days · click to expand
            </div>
            {[...RESULTS].map(d=>(
              <DayCard key={d.date} day={d}
                expanded={expanded===d.date}
                onToggle={()=>setExpanded(
                  expanded===d.date?null:d.date)}/>
            ))}
          </>
        )}
        {tab==="runlines" && (
          <div>
            <div style={{marginBottom:12,padding:"12px 16px",
              background:"#f5c51810",border:"1px solid #f5c51830",borderRadius:8}}>
              <div style={{fontSize:11,color:"#f5c518",fontFamily:T.mono,
                letterSpacing:1,marginBottom:4}}>🏟️ RUN LINE RECORD</div>
              <div style={{fontSize:11,color:"#888",fontFamily:T.mono,lineHeight:1.6}}>
                {rlStats_all.hits}-{rlStats_all.total-rlStats_all.hits} ({rlStats_all.total>0?(rlStats_all.rate*100).toFixed(0):0}% hit rate)
                {" · "}{rlStats_all.pnl>=0?"+":""}${rlStats_all.pnl.toFixed(0)} P&L
              </div>
            </div>
            {RL_RESULTS.filter(d=>d.rl&&d.rl.length>0).map((day,di)=>(
              <div key={di} style={{background:T.surface,border:"1px solid "+T.border,
                borderRadius:8,marginBottom:12,overflow:"hidden"}}>
                <div style={{padding:"10px 16px",borderBottom:"1px solid "+T.border,
                  display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                  <div style={{fontSize:13,fontWeight:800,color:T.text,fontFamily:T.head}}>
                    {day.date}
                  </div>
                  <div style={{fontSize:11,color:T.muted,fontFamily:T.mono}}>
                    {(day.rl||[]).filter(r=>r.hit===true).length}-
                    {(day.rl||[]).filter(r=>r.hit===false).length}
                    {(day.rl||[]).filter(r=>r.hit===null).length>0 &&
                      " · "+(day.rl||[]).filter(r=>r.hit===null).length+"p"}
                  </div>
                </div>
                {(day.rl||[]).map((r,i)=>{
                  const color = r.hit===true?"#00ff88":r.hit===false?"#ff4757":"#888";
                  const marker = r.hit===true?"✓":r.hit===false?"✗":"—";
                  const pnl = r.hit===true
                    ? (r.odds<0 ? 100*(100/Math.abs(r.odds)) : 100*(r.odds/100))
                    : r.hit===false ? -100 : 0;
                  return (
                    <div key={i} style={{padding:"10px 16px",
                      borderBottom:i<day.rl.length-1?"1px solid "+T.border:"none",
                      display:"flex",justifyContent:"space-between",alignItems:"center",
                      background:i%2===0?"transparent":"#ffffff02"}}>
                      <div style={{display:"flex",gap:10,alignItems:"center"}}>
                        <span style={{fontSize:14,color,fontWeight:700}}>{marker}</span>
                        <div>
                          <div style={{fontSize:13,color:T.text,fontFamily:T.head,fontWeight:700}}>
                            {r.bet}
                          </div>
                          <div style={{fontSize:10,color:T.muted,fontFamily:T.mono,marginTop:2}}>
                            {r.note}
                          </div>
                        </div>
                      </div>
                      <div style={{textAlign:"right"}}>
                        <div style={{fontSize:13,fontWeight:800,color,fontFamily:T.head}}>
                          {r.hit===null?"PENDING":pnl>=0?"+$"+pnl.toFixed(0):"-$100"}
                        </div>
                        <div style={{fontSize:10,color:T.muted,fontFamily:T.mono}}>
                          {r.odds>0?"+":""}{r.odds}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        )}
      </div>
      <div style={{margin:"20px 24px 0",padding:"12px 16px",
        background:"#ffffff04",border:"1px solid #ffffff08",
        borderRadius:8,maxWidth:1280,marginLeft:"auto",marginRight:"auto"}}>
        <div style={{fontSize:9,color:"#444",fontFamily:"'IBM Plex Mono',monospace",
          lineHeight:1.6,textAlign:"center"}}>
          ⚠️ ENTERTAINMENT PURPOSES ONLY — Edge Index provides sports analytics
          and statistical analysis for informational and entertainment purposes only.
          This is not financial advice. Sports betting involves risk.
          Please gamble responsibly. Must be 21+ and in a jurisdiction where
          sports betting is legal. If you have a gambling problem call 1-800-GAMBLER.
        </div>
      </div>
    </div>
  );
}
