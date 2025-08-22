// [CHANGED] useRef 제거 (파일업로드 기능 삭제했으므로 불필요)
import React, { useState, useContext, useEffect /* useRef 제거 */ } from "react";
import { getAuth, updateProfile, signOut } from "firebase/auth";

import { useNavigate } from "react-router-dom";
import { Fade } from "react-reveal";
import toast, { Toaster } from "react-hot-toast";

import { AuthContext } from "../Context/UserContext";
import WelcomePageBanner from "../images/WelcomePageBanner.jpg";

import "swiper/css";
import "swiper/css/navigation";
import "swiper/css/pagination";

function Profile() {
  const { User } = useContext(AuthContext);

  const [profilePic, setProfilePic] = useState("");
  const [isUserNameChanged, setIsUserNameChanged] = useState(false);
  const [userName, setUserName] = useState("");

  const navigate = useNavigate();

  useEffect(() => {
    if (User != null) {
      console.log(User.photoURL, "hello");
      setProfilePic(User.photoURL || ""); // [SAFE] null 대비
    }
  }, [User]); // [CHANGED] User 변경 시에도 반영되도록

  function notify() {
    toast.success("  Data Updated Sucessfuly  ");
  }

  // [UNCHANGED] 이름만 변경(업로드 기능 제거)
  const changeUserName = (e) => {
    e.preventDefault();
    if (isUserNameChanged && userName.trim() !== "") {
      const auth = getAuth();
      updateProfile(auth.currentUser, { displayName: userName.trim() })
        .then(() => {
          notify();
        })
        .catch((error) => {
          alert(error.message);
        });
    } else {
      setIsUserNameChanged(false);
    }
  };

  // [UNCHANGED] 기본 아바타 4개 중 선택 시 photoURL 갱신
  const updateProfilePic = (imageURL) => {
    const auth = getAuth();
    updateProfile(auth.currentUser, { photoURL: imageURL })
      .then(() => {
        setProfilePic(imageURL); // [CHANGED] 바로 상태 반영
        notify();
      })
      .catch((error) => {
        alert(error.message);
      });
  };

  const SignOut = () => {
    const auth = getAuth();
    signOut(auth)
      .then(() => {
        navigate("/");
      })
      .catch((error) => {
        alert(error.message);
      });
  };

  return (
    <div>
      <div
        className="flex h-screen justify-center items-center"
        style={{
          backgroundImage: `linear-gradient(0deg, hsl(0deg 0% 0% / 73%) 0%, hsl(0deg 0% 0% / 73%) 35%), url(${WelcomePageBanner})`,
        }}
      >
        {/* [CHANGED] 토스터는 항상 한 번만 렌더링되면 됩니다 */}
        <Toaster />

        <Fade>
          <div className="bg-[#000000bf] p-5 md:p-12 rounded-md">
            <h1 className="text-4xl text-white font-bold mb-4 md:mb-8">
              Edit your Profile
            </h1>

            <div className="flex justify-center flex-col items-center md:flex-row md:items-start">
              <img
                className="h-28 w-28 rounded-full cursor-pointer mb-3 md:mr-16"
                src={
                  profilePic
                    ? profilePic
                    // [CHANGED] 404 나던 기본 이미지 → 안정적인 기본 아바타로 교체
                    : "https://upload.wikimedia.org/wikipedia/commons/0/0b/Netflix-avatar.png"
                }
                alt="NETFLIX"
              />

              <div>
                <hr className="mb-2 h-px bg-gray-500 border-0 dark:bg-gray-700" />

                <h1 className="text-white text-lg font-medium mb-2">
                  User Name
                </h1>

                <input
                  type="text"
                  onChange={(e) => {
                    setUserName(e.target.value);
                    setIsUserNameChanged(true);
                  }}
                  className="block w-full rounded-md bg-stone-900 text-white border-gray-300 p-2 mb-6 focus:border-indigo-500 focus:ring-indigo-500 sm:text-base"
                  placeholder={User ? User.displayName : ""}
                />

                <h1 className="text-white text-lg font-medium mb-2">Email</h1>
                <h1 className="text-white text-xl bg-stone-900 p-2 rounded mb-4 md:pr-52">
                  {User ? User.email : ""}
                </h1>

                <h1 className="text-white text-xl p-2 rounded mb-4">
                  Unique ID : {User ? User.uid : ""}
                </h1>

                <hr className="h-px bg-gray-500 border-0 mb-4 md:mb-10 dark:bg-gray-700" />

                <h1 className="text-white text-lg font-medium mb-4">
                  Who is Watching ?
                </h1>

                <div className="flex justify-between cursor-pointer mb-4 md:mb-8">
                  <img
                    onClick={() =>
                      updateProfilePic(
                        "https://i.pinimg.com/originals/ba/2e/44/ba2e4464e0d7b1882cc300feceac683c.png"
                      )
                    }
                    className="w-16 h-16 rounded-md cursor-pointer"
                    src="https://i.pinimg.com/originals/ba/2e/44/ba2e4464e0d7b1882cc300feceac683c.png"
                  />
                  <img
                    onClick={() =>
                      updateProfilePic(
                        "https://i.pinimg.com/736x/db/70/dc/db70dc468af8c93749d1f587d74dcb08.jpg"
                      )
                    }
                    className="w-16 h-16 rounded-md cursor-pointer"
                    src="https://i.pinimg.com/736x/db/70/dc/db70dc468af8c93749d1f587d74dcb08.jpg"
                  />
                  <img
                    onClick={() =>
                      updateProfilePic(
                        "https://upload.wikimedia.org/wikipedia/commons/0/0b/Netflix-avatar.png"
                      )
                    }
                    className="w-16 h-16 rounded-md cursor-pointer"
                    src="https://upload.wikimedia.org/wikipedia/commons/0/0b/Netflix-avatar.png"
                  />
                  <img
                    onClick={() =>
                      updateProfilePic(
                        "https://ih0.redbubble.net/image.618363037.0853/flat,1000x1000,075,f.u2.jpg"
                      )
                    }
                    className="w-16 h-16 rounded-md cursor-pointer"
                    src="https://ih0.redbubble.net/image.618363037.0853/flat,1000x1000,075,f.u2.jpg"
                  />

                  {/* ─────────────────────────────────────────────────────
                      [REMOVED] 업로드 입력/버튼/미리보기(오류 원인)
                      - ref={inputRef}
                      - onChange={handleFileChange}
                      - onClick={handleClick}
                      - newProfielPicURL 미리보기
                     ───────────────────────────────────────────────────── */}
                </div>
              </div>
            </div>

            <div className="flex justify-between mt-4">
              <button
                onClick={SignOut}
                className="flex items-center border-[0.7px] border-white text-white font-medium sm:font-bold text-xs px-14 md:px-24 md:text-xl  py-3 rounded shadow hover:shadow-lg hover:bg-white hover:border-white hover:text-blue-700 outline-none focus:outline-none mr-3 mb-1 ease-linear transition-all duration-150"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="w-6 h-6 mr-2"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M22 10.5h-6m-2.25-4.125a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zM4 19.235v-.11a6.375 6.375 0 0112.75 0v.109A12.318 12.318 0 0110.374 21c-2.331 0-4.512-.645-6.374-1.766z"
                  />
                </svg>
                SignOut
              </button>

              {/* [CHANGED] 업로드 변수 삭제했으니 조건도 userName만 체크 */}
              {userName.trim() !== "" ? (
                <button
                  onClick={changeUserName}
                  className="flex items-center bg-blue-700 text-white font-medium sm:font-bold text-xs px-10 md:px-16 md:text-xl  py-3 rounded shadow hover:shadow-lg hover:bg-white hover:text-blue-700 outline-none focus:outline-none mr-3 mb-1 ease-linear transition-all duration-150"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className="w-6 h-6 mr-2"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12z"
                    />
                  </svg>
                  Save and continue
                </button>
              ) : (
                <button
                  onClick={() => navigate("/")}
                  className="flex items-center bg-blue-700 text-white font-medium sm:font-bold text-xs px-10 md:px-16 md:text-xl  py-3 rounded shadow hover:shadow-lg hover:bg-white hover:text-blue-700 outline-none focus:outline-none mr-3 mb-1 ease-linear transition-all duration-150"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className="w-6 h-6 mr-2"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"
                    />
                  </svg>
                  Back to Home
                </button>
              )}
            </div>
          </div>
        </Fade>
      </div>
    </div>
  );
}

export default Profile;
