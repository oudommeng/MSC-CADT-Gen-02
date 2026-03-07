
// Part: I
db.scores.insertMany([
    {
        score_id: 1,
        student_id: 10,
        student_name: 'Sok Dara',
        dept_id: 1,
        dept_name: 'Computer Science',
        subject_id: 1,
        subject_name: 'Java',
        teacher_name: 'Java Teacher',
        marks: 70
    },
    {
        score_id: 2,
        student_id: 10,
        student_name: 'Sok Dara',
        dept_id: 1,
        dept_name: 'Computer Science',
        subject_id: 2,
        subject_name: 'C++',
        teacher_name: 'C++ Teacher',
        marks: 75
    },
    {
        score_id: 3,
        student_id: 11,
        student_name: 'Chantha',
        dept_id: 2,
        dept_name: 'IT',
        subject_id: 1,
        subject_name: 'Java',
        teacher_name: 'Java Teacher',
        marks: 80
    },
    {
        score_id: 4,
        student_id: 12,
        student_name: 'Rina',
        dept_id: 2,
        dept_name: 'IT',
        subject_id: 3,
        subject_name: 'DB',
        teacher_name: 'DB Teacher',
        marks: 65
    },
    {
        score_id: 5,
        student_id: 12,
        student_name: 'Rina',
        dept_id: 2,
        dept_name: 'IT',
        subject_id: 2,
        subject_name: 'C++',
        teacher_name: 'C++ Teacher',
        marks: 90
    }
]);

//Part II
/* a.Identify Entities: Based on the attributes, the main entities are:
•	Student(student_id, student_name)
•	Department(dept_id, dept_name)
•	Subject(subject_id, subject_name)
•	Teacher(teacher_name)—though it's simplistic here, as teachers are tied to subjects without a separate ID.
•	Score(score_id, marks)—this is the central fact table linking others.
    b.Relationship Types:
•	Student belongs to Department: 1 - N(one department has many students).
•	Score is assigned to Student: 1 - N(one student has many scores).
•	Score is for Subject: 1 - N(one subject has many scores).
•	Subject is taught by Teacher: 1 - 1(assuming one teacher per subject in this data; could be 1 - N in a real model).
•	Overall, Score is an associative entity for a many - to - many relationship between Student and Subject(students take multiple subjects,
    subjects have multiple students), with additional attributes like marks.
 */

//Part III
// Create collections:

db.departments.insertMany([
    { dept_id: 1, dept_name: 'Computer Science' },
    { dept_id: 2, dept_name: 'IT' }
]);


db.students.insertMany([
    { student_id: 10, student_name: 'Sok Dara', dept_id: 1 },
    { student_id: 11, student_name: 'Chantha', dept_id: 2 },
    { student_id: 12, student_name: 'Rina', dept_id: 2 }
]);

db.subjects.insertMany([
    { subject_id: 1, subject_name: 'Java', teacher_name: 'Java Teacher' },
    { subject_id: 2, subject_name: 'C++', teacher_name: 'C++ Teacher' },
    { subject_id: 3, subject_name: 'DB', teacher_name: 'DB Teacher' }
]);

db.scores_normalized.insertMany([
    { score_id: 1, student_id: 10, subject_id: 1, marks: 70 },
    { score_id: 2, student_id: 10, subject_id: 2, marks: 75 },
    { score_id: 3, student_id: 11, subject_id: 1, marks: 80 },
    { score_id: 4, student_id: 12, subject_id: 3, marks: 65 },
    { score_id: 5, student_id: 12, subject_id: 2, marks: 90 }
]);

// "load data" from denormalized to normalized

db.scores.aggregate([
    { $group: { _id: { dept_id: "$dept_id", dept_name: "$dept_name" } } },
    { $replaceRoot: { newRoot: "$_id" } },
    { $out: "departments" } // Outputs to new collection
]);

// Similarly for students
db.scores.aggregate([
    { $group: { _id: { student_id: "$student_id", student_name: "$student_name", dept_id: "$dept_id" } } },
    { $replaceRoot: { newRoot: "$_id" } },
    { $out: "students" }
]);

// For subjects
db.scores.aggregate([
    { $group: { _id: { subject_id: "$subject_id", subject_name: "$subject_name", teacher_name: "$teacher_name" } } },
    { $replaceRoot: { newRoot: "$_id" } },
    { $out: "subjects" }
]);

// For scores_normalized (core fields)
db.scores.aggregate([
    { $project: { score_id: 1, student_id: 1, subject_id: 1, marks: 1 } },
    { $out: "scores_normalized" }
]);

// Part IV
// a. Build Score Report

db.scores_normalized.aggregate([
    { $lookup: { from: "students", localField: "student_id", foreignField: "student_id", as: "student" } },
    { $unwind: "$student" },
    { $lookup: { from: "subjects", localField: "subject_id", foreignField: "subject_id", as: "subject" } },
    { $unwind: "$subject" },
    { $lookup: { from: "departments", localField: "student.dept_id", foreignField: "dept_id", as: "department" } },
    { $unwind: "$department" },
    {
        $project: {
            score_id: 1,
            student_id: "$student.student_id",
            student_name: "$student.student_name",
            dept_id: "$department.dept_id",
            dept_name: "$department.dept_name",
            subject_id: "$subject.subject_id",
            subject_name: "$subject.subject_name",
            teacher_name: "$subject.teacher_name",
            marks: 1
        }
    }
]);

// b. Select Students with Average Score >= 50

db.scores_normalized.aggregate([
    {
        $group: {
            _id: "$student_id",
            average_score: { $avg: "$marks" }
        }
    },
    { $match: { average_score: { $gte: 50 } } }, // HAVING equivalent
    { $lookup: { from: "students", localField: "_id", foreignField: "student_id", as: "student" } },
    { $unwind: "$student" },
    { $project: { student_id: "$_id", student_name: "$student.student_name", average_score: 1 } }
]);

// c. Improve Query Performance
// First, create indexes:

// 1. Run Explain on a query WITHOUT an index: We search for scores by "Rina".
db.scores_denormalized.find({ student_name: "Rina" }).explain("executionStats");
// 2. Create the Index:
db.scores_denormalized.createIndex({ student_name: 1 });
// 3. Run Explain AGAIN:
db.scores_denormalized.find({ student_name: "Rina" }).explain("executionStats");

// d. "Reduce" total marks per Department

db.scores.aggregate([
    {
        $group: {
            _id: "$dept_name",
            totalMarks: { $sum: "$marks" }
        }
    }
]);

